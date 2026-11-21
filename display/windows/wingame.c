#define PY_SSIZE_T_CLEAN   /* '#' formats of PyArg_ParseTuple take Py_ssize_t */
#include <Python.h>
#include <windows.h>
#include <mmsystem.h>
#define DIRECTINPUT_VERSION 0x0800
#include <dinput.h>


 /************************** DISPLAY PART ***************************/

typedef struct {
	BITMAPINFOHEADER bmiHeader;
	union {
		DWORD bmiMask[3];
		short bmiIndices[255];
	};
} screenbmp_t;

/* Game controllers: their buttons, sticks and D-pads arrive as keys of
   their own, which the players choose during key definition like any
   key (the same numbers as in dpy_pygame.py).  DirectInput: no
   controller database or mapping. */
#define MAX_PADS        32
#define PAD_AXES        8         /* X Y Z Rx Ry Rz, 2 sliders */
#define PAD_HATS        4
#define PAD_BUTTONS     128
#define JOYKEY(slot, kind, n)  (0x20000000 | ((slot) << 16) | ((kind) << 12) | (n))
enum { JOY_BUTTON, JOY_AXIS_NEG, JOY_AXIS_POS, JOY_HAT };
#define AXIS_RANGE      1000
#define AXIS_PRESS      500       /* from the axis' resting position */
#define AXIS_RELEASE    300
#define REPEAT_DELAY    500       /* ms, held inputs repeat as keys do */
#define REPEAT_INTERVAL 770

typedef struct {
  LPDIRECTINPUTDEVICE8A dev;      /* NULL: a free slot */
  GUID guid;
  int polled;                     /* rest[] is known */
  LONG rest[PAD_AXES];            /* triggers often rest at one end */
  /* for each input: 0 if not held, else when it repeats next */
  DWORD axisrep[PAD_AXES][2];     /* negative, positive */
  DWORD hatrep[PAD_HATS][4];      /* left, right, up, down */
  DWORD buttonrep[PAD_BUTTONS];
} pad_t;

typedef struct {
  PyObject_HEAD
  HWND win;
  int width, height, bpp;
  HDC dc;
  HPALETTE hpal, hprevpal;
  screenbmp_t screenbmpinfo;
  unsigned char* screenbmpdata;
  unsigned char* screenfirstline;
  int screenscanline;   /* < 0 ! */
  PyObject* keyevents;
  PyObject* mouseevents;
  PyObject* motionevent;
  int vx, vy, vw, vh;     /* where the playfield is drawn in the window */
  int clearbars;          /* paint the black bars around it */
  int fullscreen;
  WINDOWPLACEMENT wp;     /* the window before going full screen */
  HMENU winmenu;          /* the "Window" submenu */
  WPARAM swallowkeyup;    /* the key that toggled full screen */
  LPDIRECTINPUT8A dinput;
  int findpads;           /* look for newly plugged controllers */
  pad_t pads[MAX_PADS];   /* the slot is part of the key numbers */
} DisplayObject;

/* the "Window" submenu of the system menu; the 4 low bits of these IDs
   are used by Windows itself */
#define IDM_SCALE1      0x0010    /* .. IDM_SCALE1 + 3*IDM_SCALESTEP: 4x */
#define IDM_SCALESTEP   0x0010
#define IDM_FULLSCREEN  0x0050
#define WINDOW_STYLE    WS_OVERLAPPEDWINDOW

/* the largest side of an image, as in common/pixmap.py; it also keeps
   3*w*h and the buffer sizes in range */
#define MAX_SIDE        4096

static int bad_size(int w, int h, int least)
{
  if (w >= least && h >= least && w <= MAX_SIDE && h <= MAX_SIDE)
    return 0;
  PyErr_Format(PyExc_ValueError, "bad image size %dx%d", w, h);
  return 1;
}

#define DisplayObject_Check(v)	(Py_TYPE(v) == &Display_Type)
static PyTypeObject Display_Type;


static void flush(DisplayObject* self)
{
  /*GdiFlush();*/
}

static void release_window_data(DisplayObject* self)
{
  if (self->hprevpal)
    {
      SelectPalette(self->dc, self->hprevpal, FALSE);
      self->hprevpal = (HPALETTE) NULL;
    }
  if (self->hpal)
    {
      DeleteObject(self->hpal);
      self->hpal = (HPALETTE) NULL;
    }
  if (self->dc && self->win)
    {
      ReleaseDC(self->win, self->dc);
      self->dc = (HDC) NULL;
    }
}

static void close_pads(DisplayObject* self)
{
  int i;
  for (i = 0; i < MAX_PADS; i++)
    if (self->pads[i].dev)
      {
        IDirectInputDevice8_Unacquire(self->pads[i].dev);
        IDirectInputDevice8_Release(self->pads[i].dev);
        self->pads[i].dev = NULL;
      }
  if (self->dinput)
    {
      IDirectInput8_Release(self->dinput);
      self->dinput = NULL;
    }
}

static void display_close(DisplayObject* self)
{
  close_pads(self);
  release_window_data(self);
  if (self->win)
    {
      SetWindowLongPtr(self->win, 0, 0);
      DestroyWindow(self->win);
      self->win = (HWND) NULL;
    }
}

static void update_view(DisplayObject* self)
{
  /* scale the playfield to the window, keeping its proportions,
     centered, black bars around it */
  RECT rc;
  int cw, ch, tw, th;
  if (!GetClientRect(self->win, &rc))
    return;
  cw = rc.right;
  ch = rc.bottom;
  if (cw * self->height <= ch * self->width)
    {
      tw = cw;
      th = (int) ((long long) self->height * cw / self->width);
    }
  else
    {
      th = ch;
      tw = (int) ((long long) self->width * ch / self->height);
    }
  self->vx = (cw - tw) / 2;
  self->vy = (ch - th) / 2;
  self->vw = tw;
  self->vh = th;
  self->clearbars = 1;
}

static int paint_screen(DisplayObject* self)
{
  HDC dc = self->dc;
  int r;
  if (self->vw <= 0 || self->vh <= 0)
    return 1;       /* minimized */
  if (self->hpal)
    RealizePalette(dc);
  if (self->clearbars)
    {
      RECT rc, bar;
      HBRUSH black = (HBRUSH) GetStockObject(BLACK_BRUSH);
      GetClientRect(self->win, &rc);
      SetRect(&bar, 0, 0, rc.right, self->vy);
      FillRect(dc, &bar, black);
      SetRect(&bar, 0, self->vy + self->vh, rc.right, rc.bottom);
      FillRect(dc, &bar, black);
      SetRect(&bar, 0, self->vy, self->vx, self->vy + self->vh);
      FillRect(dc, &bar, black);
      SetRect(&bar, self->vx + self->vw, self->vy, rc.right, self->vy + self->vh);
      FillRect(dc, &bar, black);
      self->clearbars = 0;
    }
  if (self->vw == self->width && self->vh == self->height)
    r = SetDIBitsToDevice(dc, self->vx, self->vy, self->width, self->height,
                          0, 0, 0, self->height, self->screenbmpdata,
                          (BITMAPINFO*)(&self->screenbmpinfo), DIB_PAL_COLORS);
  else
    {
      /* exact multiples (the 1x..4x sizes): sharp pixels; else smooth */
      if (self->vw % self->width == 0 &&
          self->vw / self->width * self->height == self->vh)
        SetStretchBltMode(dc, COLORONCOLOR);
      else
        {
          SetStretchBltMode(dc, HALFTONE);
          SetBrushOrgEx(dc, 0, 0, NULL);
        }
      r = StretchDIBits(dc, self->vx, self->vy, self->vw, self->vh,
                        0, 0, self->width, self->height, self->screenbmpdata,
                        (BITMAPINFO*)(&self->screenbmpinfo), DIB_PAL_COLORS,
                        SRCCOPY);
    }
  return r != 0;
}

static void set_fullscreen(DisplayObject* self, int on)
{
  HWND hwnd = self->win;
  DWORD style = GetWindowLong(hwnd, GWL_STYLE);
  if (on && !self->fullscreen)
    {
      MONITORINFO mi;
      mi.cbSize = sizeof(mi);
      self->wp.length = sizeof(self->wp);
      if (!GetWindowPlacement(hwnd, &self->wp) ||
          !GetMonitorInfo(MonitorFromWindow(hwnd, MONITOR_DEFAULTTOPRIMARY), &mi))
        return;
      if (self->wp.showCmd != SW_SHOWMAXIMIZED)
        self->wp.showCmd = SW_SHOWNORMAL;   /* not hidden (--fullscreen) */
      SetWindowLong(hwnd, GWL_STYLE, (style & ~WINDOW_STYLE) | WS_POPUP);
      SetWindowPos(hwnd, HWND_TOP, mi.rcMonitor.left, mi.rcMonitor.top,
                   mi.rcMonitor.right - mi.rcMonitor.left,
                   mi.rcMonitor.bottom - mi.rcMonitor.top,
                   SWP_NOOWNERZORDER | SWP_FRAMECHANGED);
      self->fullscreen = 1;
    }
  else if (!on && self->fullscreen)
    {
      SetWindowLong(hwnd, GWL_STYLE, (style & ~WS_POPUP) | WINDOW_STYLE);
      SetWindowPlacement(hwnd, &self->wp);
      SetWindowPos(hwnd, NULL, 0, 0, 0, 0,
                   SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER |
                   SWP_NOOWNERZORDER | SWP_FRAMECHANGED);
      self->fullscreen = 0;
    }
  update_view(self);
}

static void set_scale(DisplayObject* self, int n)
{
  RECT wr;
  set_fullscreen(self, 0);
  if (IsZoomed(self->win) || IsIconic(self->win))
    ShowWindow(self->win, SW_RESTORE);
  SetRect(&wr, 0, 0, self->width * n, self->height * n);
  AdjustWindowRectEx(&wr, (DWORD) GetWindowLong(self->win, GWL_STYLE), FALSE, 0);
  SetWindowPos(self->win, NULL, 0, 0, wr.right - wr.left, wr.bottom - wr.top,
               SWP_NOMOVE | SWP_NOZORDER | SWP_NOACTIVATE);
  update_view(self);
}

static void update_winmenu(DisplayObject* self)
{
  RECT rc;
  int n;
  int zoomed = IsZoomed(self->win);
  GetClientRect(self->win, &rc);
  for (n = 1; n <= 4; n++)
    {
      UINT id = IDM_SCALE1 + (n-1) * IDM_SCALESTEP;
      int checked = !self->fullscreen && !zoomed &&
                    rc.right == self->width * n && rc.bottom == self->height * n;
      CheckMenuItem(self->winmenu, id, checked ? MF_CHECKED : MF_UNCHECKED);
    }
  CheckMenuItem(self->winmenu, IDM_FULLSCREEN,
                self->fullscreen ? MF_CHECKED : MF_UNCHECKED);
}

static int window_command(DisplayObject* self, WPARAM cmd)
{
  cmd &= 0xFFF0;
  if (cmd >= IDM_SCALE1 && cmd <= IDM_SCALE1 + 3 * IDM_SCALESTEP)
    set_scale(self, (int) ((cmd - IDM_SCALE1) / IDM_SCALESTEP) + 1);
  else if (cmd == IDM_FULLSCREEN)
    set_fullscreen(self, !self->fullscreen);
  else
    return 0;
  return 1;
}

static void add_key_event(DisplayObject* self, WPARAM key, int etype)
{
  PyObject* v;
  if (self->keyevents == NULL)
    {
      self->keyevents = PyList_New(0);
      if (self->keyevents == NULL)
        return;
    }
  v = Py_BuildValue("ii", (int) key, etype);
  if (v == NULL)
    return;
  PyList_Append(self->keyevents, v);
  Py_DECREF(v);
}

static void reset_idle_timer(void)
{
  SetThreadExecutionState(ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED);
}

static void pad_key(DisplayObject* self, int keysym, DWORD* rep, int down)
{
  if (down && !*rep)
    {
      *rep = (GetTickCount() + REPEAT_DELAY) | 1;   /* never 0 */
      add_key_event(self, (WPARAM) keysym, 2);
      reset_idle_timer();
    }
  else if (!down && *rep)
    {
      *rep = 0;
      add_key_event(self, (WPARAM) keysym, 3);
      reset_idle_timer();
    }
}

static void pad_repeat(DisplayObject* self, int keysym, DWORD* rep, DWORD now)
{
  if (*rep && (LONG) (now - *rep) >= 0)
    {
      *rep = (now + REPEAT_INTERVAL) | 1;
      add_key_event(self, (WPARAM) keysym, 2);
      reset_idle_timer();
    }
}

static void pad_release_all(DisplayObject* self, int slot)
{
  pad_t* pad = &self->pads[slot];
  int i, n;
  for (i = 0; i < PAD_AXES; i++)
    for (n = 0; n < 2; n++)
      pad_key(self, JOYKEY(slot, JOY_AXIS_NEG + n, i), &pad->axisrep[i][n], 0);
  for (i = 0; i < PAD_HATS; i++)
    for (n = 0; n < 4; n++)
      pad_key(self, JOYKEY(slot, JOY_HAT, i*4 + n), &pad->hatrep[i][n], 0);
  for (i = 0; i < PAD_BUTTONS; i++)
    pad_key(self, JOYKEY(slot, JOY_BUTTON, i), &pad->buttonrep[i], 0);
}

static BOOL CALLBACK add_pad(LPCDIDEVICEINSTANCEA inst, LPVOID context)
{
  DisplayObject* self = (DisplayObject*) context;
  LPDIRECTINPUTDEVICE8A dev;
  DIPROPRANGE range;
  int i, slot = -1;
  for (i = 0; i < MAX_PADS; i++)
    {
      if (self->pads[i].dev == NULL)
        {
          if (slot < 0)
            slot = i;
        }
      else if (!memcmp(&self->pads[i].guid, &inst->guidInstance, sizeof(GUID)))
        return DIENUM_CONTINUE;       /* already open */
    }
  if (slot < 0)
    return DIENUM_STOP;
  if (FAILED(IDirectInput8_CreateDevice(self->dinput, &inst->guidInstance,
                                        &dev, NULL)))
    return DIENUM_CONTINUE;
  if (FAILED(IDirectInputDevice8_SetDataFormat(dev, &c_dfDIJoystick2)) ||
      FAILED(IDirectInputDevice8_SetCooperativeLevel(dev, self->win,
                                    DISCL_FOREGROUND | DISCL_NONEXCLUSIVE)))
    {
      IDirectInputDevice8_Release(dev);
      return DIENUM_CONTINUE;
    }
  range.diph.dwSize = sizeof(range);
  range.diph.dwHeaderSize = sizeof(range.diph);
  range.diph.dwObj = 0;
  range.diph.dwHow = DIPH_DEVICE;     /* all the axes */
  range.lMin = -AXIS_RANGE;
  range.lMax = AXIS_RANGE;
  IDirectInputDevice8_SetProperty(dev, DIPROP_RANGE, &range.diph);
  memset(&self->pads[slot], 0, sizeof(pad_t));
  self->pads[slot].dev = dev;
  self->pads[slot].guid = inst->guidInstance;
  return DIENUM_CONTINUE;
}

static void poll_pad(DisplayObject* self, int slot)
{
  pad_t* pad = &self->pads[slot];
  DIJOYSTATE2 js;
  LONG axes[PAD_AXES];
  DWORD now;
  HRESULT hr;
  int i, n;

  IDirectInputDevice8_Poll(pad->dev);
  hr = IDirectInputDevice8_GetDeviceState(pad->dev, sizeof(js), &js);
  if (hr == DIERR_INPUTLOST || hr == DIERR_NOTACQUIRED)
    {
      /* not ours while the window is in the background; unplugged */
      pad_release_all(self, slot);
      if (IDirectInputDevice8_Acquire(pad->dev) == (HRESULT) DIERR_UNPLUGGED)
        {
          IDirectInputDevice8_Release(pad->dev);
          pad->dev = NULL;
        }
      return;
    }
  if (FAILED(hr))
    return;

  axes[0] = js.lX;  axes[1] = js.lY;  axes[2] = js.lZ;
  axes[3] = js.lRx; axes[4] = js.lRy; axes[5] = js.lRz;
  axes[6] = js.rglSlider[0];
  axes[7] = js.rglSlider[1];
  if (!pad->polled)
    {
      for (i = 0; i < PAD_AXES; i++)
        if (axes[i] > AXIS_PRESS || axes[i] < -AXIS_PRESS)
          pad->rest[i] = axes[i];
      pad->polled = 1;
    }
  for (i = 0; i < PAD_AXES; i++)
    {
      LONG offset = axes[i] - pad->rest[i];
      int neg = pad->axisrep[i][0] != 0, pos = pad->axisrep[i][1] != 0;
      if ((neg && offset > -AXIS_RELEASE) || (pos && offset < AXIS_RELEASE))
        neg = pos = 0;
      if (!neg && !pos)
        {
          neg = offset < -AXIS_PRESS;
          pos = offset > AXIS_PRESS;
        }
      /* a release before a press, when the stick goes from one side
         to the other */
      for (n = 0; n < 2; n++)
        if (!(n ? pos : neg))
          pad_key(self, JOYKEY(slot, JOY_AXIS_NEG + n, i), &pad->axisrep[i][n], 0);
      for (n = 0; n < 2; n++)
        if (n ? pos : neg)
          pad_key(self, JOYKEY(slot, JOY_AXIS_NEG + n, i), &pad->axisrep[i][n], 1);
    }
  for (i = 0; i < PAD_HATS; i++)
    {
      /* hundredths of degrees clockwise from up, or centered */
      DWORD a = js.rgdwPOV[i];
      int dir[4] = {0, 0, 0, 0};
      if (LOWORD(a) != 0xFFFF)
        {
          dir[2] = a >= 31500 || a <= 4500;          /* up */
          dir[1] = a >= 4500 && a <= 13500;          /* right */
          dir[3] = a >= 13500 && a <= 22500;         /* down */
          dir[0] = a >= 22500 && a <= 31500;         /* left */
        }
      for (n = 0; n < 4; n++)
        if (!dir[n])
          pad_key(self, JOYKEY(slot, JOY_HAT, i*4 + n), &pad->hatrep[i][n], 0);
      for (n = 0; n < 4; n++)
        if (dir[n])
          pad_key(self, JOYKEY(slot, JOY_HAT, i*4 + n), &pad->hatrep[i][n], 1);
    }
  for (i = 0; i < PAD_BUTTONS; i++)
    pad_key(self, JOYKEY(slot, JOY_BUTTON, i), &pad->buttonrep[i],
            (js.rgbButtons[i] & 0x80) != 0);

  now = GetTickCount();
  for (i = 0; i < PAD_AXES; i++)
    for (n = 0; n < 2; n++)
      pad_repeat(self, JOYKEY(slot, JOY_AXIS_NEG + n, i), &pad->axisrep[i][n], now);
  for (i = 0; i < PAD_HATS; i++)
    for (n = 0; n < 4; n++)
      pad_repeat(self, JOYKEY(slot, JOY_HAT, i*4 + n), &pad->hatrep[i][n], now);
  for (i = 0; i < PAD_BUTTONS; i++)
    pad_repeat(self, JOYKEY(slot, JOY_BUTTON, i), &pad->buttonrep[i], now);
}

static void poll_pads(DisplayObject* self)
{
  int i;
  if (!self->dinput)
    return;
  if (self->findpads)
    {
      self->findpads = 0;
      IDirectInput8_EnumDevices(self->dinput, DI8DEVCLASS_GAMECTRL, add_pad,
                                self, DIEDFL_ATTACHEDONLY);
    }
  for (i = 0; i < MAX_PADS; i++)
    if (self->pads[i].dev)
      poll_pad(self, i);
}

static int playfield_xy(DisplayObject* self, LPARAM lParam, int* x, int* y)
{
  /* window coordinates to playfield coordinates; 0 in the black bars */
  int wx = (short) LOWORD(lParam) - self->vx;
  int wy = (short) HIWORD(lParam) - self->vy;
  if (wx < 0 || wy < 0 || wx >= self->vw || wy >= self->vh)
    return 0;
  *x = (int) ((long long) wx * self->width / self->vw);
  *y = (int) ((long long) wy * self->height / self->vh);
  return 1;
}

#define KEY_REPEATED(lParam)   ((lParam) & (1 << 30))
#define ALT_DOWN(lParam)       ((lParam) & (1 << 29))

static LRESULT CALLBACK display_proc(HWND hwnd, UINT uMsg,
                                     WPARAM wParam, LPARAM lParam)
{
  DisplayObject* self;
  switch (uMsg) {

  case WM_SIZE:
    self = (DisplayObject*) GetWindowLongPtr(hwnd, 0);
    if (self)
      update_view(self);
    break;

  case WM_ERASEBKGND:
    return 1;       /* paint_screen() paints everything */

  case WM_PAINT:
    {
      PAINTSTRUCT ps;
      BeginPaint(hwnd, &ps);
      EndPaint(hwnd, &ps);
      self = (DisplayObject*) GetWindowLongPtr(hwnd, 0);
      if (self && self->dc)
        {
          self->clearbars = 1;
          paint_screen(self);
        }
    }
    break;

  case WM_SYSKEYDOWN:
    /* Alt+Enter: full screen */
    self = (DisplayObject*) GetWindowLongPtr(hwnd, 0);
    if (self && wParam == VK_RETURN && ALT_DOWN(lParam))
      {
        if (!KEY_REPEATED(lParam))
          set_fullscreen(self, !self->fullscreen);
        break;
      }
    return DefWindowProc(hwnd, uMsg, wParam, lParam);

  case WM_SYSCOMMAND:
    self = (DisplayObject*) GetWindowLongPtr(hwnd, 0);
    if (self && window_command(self, wParam))
      break;
    return DefWindowProc(hwnd, uMsg, wParam, lParam);

  case WM_INITMENUPOPUP:
    self = (DisplayObject*) GetWindowLongPtr(hwnd, 0);
    if (self && (HMENU) wParam == self->winmenu)
      update_winmenu(self);
    return DefWindowProc(hwnd, uMsg, wParam, lParam);

  case WM_KEYDOWN:
    self = (DisplayObject*) GetWindowLongPtr(hwnd, 0);
    if (self)
      {
        /* F11, or Esc in full screen: toggle full screen, not a game key */
        if (wParam == VK_F11 || (wParam == VK_ESCAPE && self->fullscreen))
          {
            if (!KEY_REPEATED(lParam))
              {
                set_fullscreen(self, !self->fullscreen);
                self->swallowkeyup = wParam;
              }
            break;
          }
        add_key_event(self, wParam, 2);
      }
    break;

  case WM_KEYUP:
    self = (DisplayObject*) GetWindowLongPtr(hwnd, 0);
    if (self)
      {
        if (wParam == self->swallowkeyup)
          {
            self->swallowkeyup = 0;
            break;
          }
        add_key_event(self, wParam, 3);
      }
    break;

  case WM_LBUTTONDOWN:
    self = (DisplayObject*) GetWindowLongPtr(hwnd, 0);
    if (self)
      {
        PyObject* v;
        int x, y;
        if (self->mouseevents == NULL)
          {
            self->mouseevents = PyList_New(0);
            if (self->mouseevents == NULL)
              break;
          }
        if (!playfield_xy(self, lParam, &x, &y))
          break;
        v = Py_BuildValue("ii", x, y);
        if (v == NULL)
          break;
        PyList_Append(self->mouseevents, v);
        Py_DECREF(v);
      }
    break;

  case WM_MOUSEMOVE:
    self = (DisplayObject*) GetWindowLongPtr(hwnd, 0);
    if (self)
      {
        int x, y;
        if (!playfield_xy(self, lParam, &x, &y))
          break;
        Py_XDECREF(self->motionevent);
        self->motionevent = Py_BuildValue("ii", x, y);
      }
    break;

  case WM_DEVICECHANGE:
    /* a device was plugged or unplugged: maybe a controller */
    self = (DisplayObject*) GetWindowLongPtr(hwnd, 0);
    if (self)
      self->findpads = 1;
    return DefWindowProc(hwnd, uMsg, wParam, lParam);

  case WM_DESTROY:
    self = (DisplayObject*) GetWindowLongPtr(hwnd, 0);
    if (self)
      {
        release_window_data(self);
        self->win = (HWND) NULL;
      }
    break;

  default:
    return DefWindowProc(hwnd, uMsg, wParam, lParam);
  }

  return 0;
}

static PyObject* new_display(PyObject* dummy, PyObject* args)
{
  char* CLASSNAME = "winxshm";
  WNDCLASS wcls;
  DisplayObject* self;
  int width, height, bytes, bpp, fullscreen=0, controller=1;
  if (!PyArg_ParseTuple(args, "ii|ii", &width, &height, &fullscreen,
                        &controller))
    return NULL;

  self = PyObject_New(DisplayObject, &Display_Type);
  if (self == NULL)
    return NULL;

  memset(&self->win, 0, ((char*)(self+1)) - ((char*)(&self->win)));
  self->width = width;
  self->height = height;

  /* set window class */
  memset(&wcls, 0, sizeof(wcls));
  wcls.style = CS_BYTEALIGNCLIENT;
  wcls.lpfnWndProc = &display_proc;
  wcls.cbWndExtra = sizeof(DisplayObject*);
  //wcls.hInstance = HINSTANCE;
  wcls.hCursor = LoadCursor(0, IDC_ARROW);
  wcls.hbrBackground = (HBRUSH) GetStockObject(BLACK_BRUSH);
  wcls.lpszClassName = CLASSNAME;
  RegisterClass(&wcls);

  /* Create the window */
  {
    DWORD style = WINDOW_STYLE;
    RECT rc = {0, 0, width, height}, wr;
    AdjustWindowRectEx(&rc, style, FALSE, 0);
    self->win = CreateWindowEx(0, CLASSNAME, NULL, style,
                               CW_USEDEFAULT, CW_USEDEFAULT,
                               rc.right - rc.left, rc.bottom - rc.top,
                               (HWND) NULL, (HMENU) NULL,
                               /*HINSTANCE*/ 0, (LPVOID) NULL);
    if (self->win == (HWND) NULL) goto err2;
    if (GetClientRect(self->win, &rc) && GetWindowRect(self->win, &wr) &&
        (rc.right != width || rc.bottom != height))
      SetWindowPos(self->win, NULL, 0, 0,
                   wr.right - wr.left + width - rc.right,
                   wr.bottom - wr.top + height - rc.bottom,
                   SWP_NOMOVE | SWP_NOZORDER | SWP_NOACTIVATE);
  }
  SetWindowLongPtr(self->win, 0, (LONG_PTR) self);

  /* the "Window" submenu of the system menu (right click on the title
     bar) */
  {
    HMENU sysmenu = GetSystemMenu(self->win, FALSE);
    self->winmenu = CreatePopupMenu();
    if (sysmenu && self->winmenu)
      {
        AppendMenu(self->winmenu, MF_STRING, IDM_SCALE1, "&1x");
        AppendMenu(self->winmenu, MF_STRING, IDM_SCALE1 + IDM_SCALESTEP, "&2x");
        AppendMenu(self->winmenu, MF_STRING, IDM_SCALE1 + 2*IDM_SCALESTEP, "&3x");
        AppendMenu(self->winmenu, MF_STRING, IDM_SCALE1 + 3*IDM_SCALESTEP, "&4x");
        AppendMenu(self->winmenu, MF_SEPARATOR, 0, NULL);
        AppendMenu(self->winmenu, MF_STRING, IDM_FULLSCREEN, "&Fullscreen\tF11");
        AppendMenu(sysmenu, MF_SEPARATOR, 0, NULL);
        AppendMenu(sysmenu, MF_POPUP, (UINT_PTR) self->winmenu, "&Window");
      }
  }
  if (controller &&
      FAILED(DirectInput8Create(GetModuleHandle(NULL), DIRECTINPUT_VERSION,
                                &IID_IDirectInput8A, (void**) &self->dinput,
                                NULL)))
    self->dinput = NULL;      /* no controllers, only the keyboard */
  self->findpads = 1;

  update_view(self);
  if (fullscreen)
    set_fullscreen(self, 1);
  ShowWindow(self->win, SW_SHOW);

  /* Create DC */
  self->dc = GetDC(self->win);
  if (!self->dc) goto err2;
  self->bpp = bpp = GetDeviceCaps(self->dc, BITSPIXEL);
  if (bpp == 8)
  {
	struct {
		WORD         palVersion; 
		WORD         palNumEntries; 
		PALETTEENTRY palPalEntry[255];
	} pal;
	pal.palNumEntries = GetSystemPaletteEntries(self->dc, 0, 255, pal.palPalEntry);
	if (pal.palNumEntries != 0)
	{
		int i;
		pal.palVersion = 0x300;
		self->hpal = CreatePalette((LOGPALETTE*)(&pal));
		self->screenbmpinfo.bmiHeader.biClrUsed = pal.palNumEntries;
		self->hprevpal = SelectPalette(self->dc, self->hpal, FALSE);
		for (i=0; i<pal.palNumEntries; i++) {
			self->screenbmpinfo.bmiIndices[i] = i;
		}
	}
  }
  if (bpp != 15 && bpp != 16 && bpp != 24 && bpp != 32 && !self->hpal)
  {
	bpp = 24;   /* default */
	fprintf(stderr, "WARNING: a hi/true color screen mode of 15, 16, 24 or 32 bits per pixels\n");
	fprintf(stderr, "         is highly recommended !\n");
  }

  /* Allocate screen bitmaps */
  bytes = (bpp+7)/8;          /* per pixel */
  bytes = (bytes*width+3)&~3; /* per scan line */
  self->screenscanline = -bytes;
  bytes = bytes*height;       /* for the whole screen */
  self->screenbmpdata = PyMem_Malloc(bytes);
  self->screenfirstline = self->screenbmpdata + bytes + self->screenscanline;
  if (self->screenbmpdata == NULL)
  {
	PyErr_NoMemory();
	goto err2;
  }
  memset(self->screenbmpdata, 0, bytes);   /* black until the first flip() */
  self->screenbmpinfo.bmiHeader.biSize = sizeof(BITMAPINFOHEADER);
  self->screenbmpinfo.bmiHeader.biWidth = self->width;
  self->screenbmpinfo.bmiHeader.biHeight = self->height;
  self->screenbmpinfo.bmiHeader.biPlanes = 1;
  self->screenbmpinfo.bmiHeader.biBitCount = (bpp+7)&~7;
  if (bpp == 16)
  {
	self->screenbmpinfo.bmiHeader.biCompression = BI_BITFIELDS;
	self->screenbmpinfo.bmiMask[0] = 0xF800;
	self->screenbmpinfo.bmiMask[1] = 0x07E0;
	self->screenbmpinfo.bmiMask[2] = 0x001F;
  }

  flush(self);
  return (PyObject*) self;

 err2:
  display_close(self);
  Py_DECREF(self);
  if (!PyErr_Occurred())
	PyErr_SetString(PyExc_IOError, "cannot open window");
  return NULL;
}

static void display_dealloc(DisplayObject* self)
{
  display_close(self);
  Py_XDECREF(self->keyevents);
  Py_XDECREF(self->mouseevents);
  Py_XDECREF(self->motionevent);
  PyMem_Free(self->screenbmpdata);
  PyObject_Del(self);
}

static PyObject* display_close1(DisplayObject* self, PyObject* args)
{
  display_close(self);
  Py_INCREF(Py_None);
  return Py_None;
}

static int checkopen(DisplayObject* self)
{
  if (self->win)
    return 1;
  //PyErr_SetString(PyExc_IOError, "the window was closed");
  PyErr_SetString(PyExc_SystemExit, "window closed.");
  return 0;
}

static PyObject* display_clear1(DisplayObject* self, PyObject* args)
{
  if (!checkopen(self))
    return NULL;
  memset(self->screenbmpdata, 0, (-self->screenscanline) * self->height);
  Py_INCREF(Py_None);
  return Py_None;
}

static void pack_pixel(DisplayObject* self, unsigned char *data, int r, int g, int b,
		       int depth)
{
  unsigned short pixel;
  switch( depth )
    {
    case 8:
      data[0] = GetNearestPaletteIndex(self->hpal, (b<<16) | (g<<8) | r);
      break;
    case 15:
      pixel = ((r<<7) & 0x7c00) | ((g<<2) & 0x03e0) | ((b>>3) & 0x001f);
      data[0] = (pixel) & 0xff;
      data[1] = (pixel>>8) & 0xff;
      break;
    case 16:
      /* assumes 5,6,5 model. */
      pixel = ((r<<8) & 0xf800) | ((g<<3) & 0x07e0) | ((b>>3) & 0x001f);
      data[0] = (pixel) & 0xff;
      data[1] = (pixel>>8) & 0xff;
      break;
    case 24:
      if( 1 )
	{
	  data[0] = b;
	  data[1] = g;
	  data[2] = r;
	  break;
	}
    case 32:
      *((unsigned int *)data) = (r<<16) | (g<<8) | b;
      break;
    }
}

static PyObject* display_pixmap1(DisplayObject* self, PyObject* args)
{
  int w,h;
  Py_ssize_t length;
  unsigned char* input = NULL;
  int keycol = -1;

  if (!checkopen(self))
    return NULL;
  if (!PyArg_ParseTuple(args, "ii|s#i", &w, &h, &input, &length, &keycol))
    return NULL;
  if (bad_size(w, h, 1))
    return NULL;

  if (1)     /* SHM */
    {
      int x, y;
      unsigned char *dst;
      int size, bytes_per_pixel;
      int packed_keycol = keycol;
      PyObject* result;
      PyObject* str;

      if (input == NULL )
        {
          Py_INCREF(Py_None);
          return Py_None;
        }

      bytes_per_pixel = self->screenbmpinfo.bmiHeader.biBitCount/8;
      size = bytes_per_pixel*w*h;

      if( 3*w*h != length )
	{
	  PyErr_SetString(PyExc_TypeError, "bad string length");
	  return NULL;
	}
      /* Create a new string and fill it with the correctly packed image */
      str = PyBytes_FromStringAndSize(NULL, size);
      if (!str)
        return NULL;
      if (keycol >= 0)
	switch( self->bpp )
	  {
	  case 8:
	    packed_keycol = 0xFF;
	    break;
	  case 15:
	    packed_keycol = (1 << 10) | (1 << 5) | 1;
	    break;
	  case 16:
	    packed_keycol = (1 << 11) | (1 << 5) | 1;
	    break;
	  default:
	    packed_keycol = keycol;
	    break;
	  }
      result = Py_BuildValue("iiOi", w, h, str, packed_keycol);
      Py_DECREF(str);  /* one ref left in 'result' */
      if (!result)
        return NULL;
      dst = (unsigned char*) PyBytes_AS_STRING(str);
      memset(dst,0,size);

      for( y=0; y<h; y++ )
	for( x=0; x<w; x++, input+=3, dst += bytes_per_pixel )
	  {
	    int r = input[0];
	    int g = input[1];
	    int b = input[2];
	    if( ((r<<16)|(g<<8)|b) == keycol )
	      for( b=0; b<bytes_per_pixel; b++ )
		dst[b] = ((unsigned char *)&packed_keycol)[b];
	    else
	      pack_pixel(self, dst, r, g, b, self->bpp);
	  }
      return result;
    }
}

static void blend_pixel(unsigned char* dst, const unsigned char* src,
                        int a, int bpp)
{
  /* dst = src*a + dst*(1-a), a in 0..256 */
  int na = 256 - a;
  unsigned s, d, r, g, b;
  switch (bpp)
    {
    case 15:
      s = src[0] | (src[1] << 8);
      d = dst[0] | (dst[1] << 8);
      r = (((s >> 10) & 31) * a + ((d >> 10) & 31) * na) >> 8;
      g = (((s >> 5) & 31) * a + ((d >> 5) & 31) * na) >> 8;
      b = ((s & 31) * a + (d & 31) * na) >> 8;
      d = (r << 10) | (g << 5) | b;
      dst[0] = d & 0xff;
      dst[1] = d >> 8;
      break;
    case 16:
      s = src[0] | (src[1] << 8);
      d = dst[0] | (dst[1] << 8);
      r = (((s >> 11) & 31) * a + ((d >> 11) & 31) * na) >> 8;
      g = (((s >> 5) & 63) * a + ((d >> 5) & 63) * na) >> 8;
      b = ((s & 31) * a + (d & 31) * na) >> 8;
      d = (r << 11) | (g << 5) | b;
      dst[0] = d & 0xff;
      dst[1] = d >> 8;
      break;
    case 24:
    case 32:
      dst[0] = (src[0] * a + dst[0] * na) >> 8;
      dst[1] = (src[1] * a + dst[1] * na) >> 8;
      dst[2] = (src[2] * a + dst[2] * na) >> 8;
      break;
    default:      /* 8 bits: a palette, no blending */
      dst[0] = src[0];
      break;
    }
}

static PyObject* display_putppm1(DisplayObject* self, PyObject* args)
{
  if (!checkopen(self))
    return NULL;

  if (1)     /* SHM */
    {
      int x,y,w,h,scanline;
      int clipx=0, clipy=0, clipw=65536, cliph=65536;
      unsigned char* src;
      Py_ssize_t length;
      int keycol;
      int alpha = 255;
      PyObject* pixmap;
      int bytes_per_pixel = self->screenbmpinfo.bmiHeader.biBitCount/8;
      unsigned char* data = self->screenfirstline;
      /* pixmap: (w, h, data, keycol), or (w, h, data, keycol, alpha)
         from getopticon() for a slightly transparent icon, drawn whole:
         pclient.py then gives None as the rect */
      PyObject* rect = Py_None;
      if (!PyArg_ParseTuple(args, "iiO!|O", &x, &y, &PyTuple_Type, &pixmap,
                            &rect) || !data)
        return NULL;
      if (rect != Py_None)
        {
          /* any 4-item sequence, as the "(iiii)" format took */
          PyObject* t = PySequence_Tuple(rect);
          int ok = t && PyArg_ParseTuple(t, "iiii", &clipx, &clipy, &clipw, &cliph);
          Py_XDECREF(t);
          if (!ok)
            return NULL;
        }
      if (!PyArg_ParseTuple(pixmap, "iis#i|i", &w, &h, &src, &length,
                            &keycol, &alpha))
        return NULL;
      if (bad_size(w, h, 1))
        return NULL;
  
      scanline = bytes_per_pixel*w;
      if (scanline*h != length)
        {
          PyErr_SetString(PyExc_TypeError, "bad string length");
          return NULL;
        }
      x -= clipx;
      y -= clipy;
      clipx += x;
      clipy += y;
      clipw += clipx;
      cliph += clipy;
      if (clipx<0) clipx=0;
      if (clipy<0) clipy=0;
      if (clipw>self->width) clipw=self->width;
      if (cliph>self->height) cliph=self->height;
      if (x<clipx) { src+=(clipx-x)*bytes_per_pixel; w+=x-clipx; x=clipx; }
      if (y<clipy) { src+=(clipy-y)*scanline; h+=y-clipy; y=clipy; }
      if (x+w > clipw) w = clipw-x;
      if (y+h > cliph) h = cliph-y;
      data += bytes_per_pixel*x+y*self->screenscanline;
      while (h>0)
        {
          int i;
	  int b;
          unsigned char* src0 = src;
	  unsigned char* data0 = data;
          if (alpha < 255)
            {
              unsigned char *keycol_bytes = (unsigned char *)&keycol;
              int a = alpha + (alpha >> 7);
              for (i=0; i<w; i++, data += bytes_per_pixel, src += bytes_per_pixel)
                if (keycol < 0 || memcmp(src, keycol_bytes, bytes_per_pixel))
                  blend_pixel(data, src, a, self->bpp);
            }
          else if (keycol < 0)
            for (i=0; i<w; i++)
	      for (b=0; b<bytes_per_pixel; b++)
		*data++ = *src++;
          else
	    {
	      unsigned char *keycol_bytes = (unsigned char *)&keycol;
	      for (i=0; i<w; i++)
		{
		  int transparent = 1;
		  for( b=0; b<bytes_per_pixel; b++ )
		    transparent = transparent && (keycol_bytes[b] == src[b]);

		  if (!transparent)
		    for( b=0; b<bytes_per_pixel; b++ )
		      *data++ = *src++;
		  else
		    {
		      data += bytes_per_pixel;
		      src += bytes_per_pixel;
		    }
		}
	    }
          src = src0 + scanline;
          data = data0 + self->screenscanline;
          h--;
        }
    }
  
  Py_INCREF(Py_None);
  return Py_None;
}

static PyObject* display_getppm1(DisplayObject* self, PyObject* args)
{
  if (!checkopen(self))
    return NULL;

  if (1)     /* SHM */
    {
      int x,y,w,h,scanline;
      int clipx=0, clipy=0, clipw=self->width, cliph=self->height;
      unsigned char* dst;
      int length;
      PyObject* ignored;
      PyObject* result;
      PyObject* str;
      int bytes_per_pixel = self->screenbmpinfo.bmiHeader.biBitCount/8;
      unsigned char* data = self->screenfirstline;
      if (!PyArg_ParseTuple(args, "(iiii)|O", &x, &y, &w, &h,
                            &ignored) || !data)
        return NULL;
      if (bad_size(w, h, 0))
        return NULL;

      scanline = bytes_per_pixel*w;
      length = scanline*h;
      str = PyBytes_FromStringAndSize(NULL, length);
      if (!str)
        return NULL;
      result = Py_BuildValue("iiOi", w, h, str, -1);
      Py_DECREF(str);  /* one ref left in 'result' */
      if (!result)
        return NULL;
      dst = (unsigned char*) PyBytes_AS_STRING(str);

      if (x<clipx) { dst+=(clipx-x)*bytes_per_pixel; w+=x-clipx; x=clipx; }
      if (y<clipy) { dst+=(clipy-y)*scanline; h+=y-clipy; y=clipy; }
      if (x+w > clipw) w = clipw-x;
      if (y+h > cliph) h = cliph-y;
      data += bytes_per_pixel*x+y*self->screenscanline;
      while (h>0)
        {
          int i;
	  int b;
          unsigned char* dst0 = dst;
	  unsigned char* data0 = data;
          for (i=0; i<w; i++)
            {
	      for( b=0; b<bytes_per_pixel; b++ )
		*dst++ = *data++;
            }
          dst = dst0 + scanline;
          data = data0 + self->screenscanline;
          h--;
        }
      return result;
    }
}

static int readXevents(DisplayObject* self)
{
  MSG Msg;
  while (PeekMessage(&Msg, (HWND) NULL, 0, 0, PM_REMOVE))
    {
      DispatchMessage(&Msg);
      if (PyErr_Occurred())
        return 0;
    }
  return checkopen(self);
}

#define ENABLE_EVENTS(mask)    do { } while (0)   /* nothing */

static PyObject* display_keyevents1(DisplayObject* self, PyObject* args)
{
  PyObject* result;
  ENABLE_EVENTS(KeyPressMask|KeyReleaseMask);
  if (!readXevents(self))
    return NULL;
  poll_pads(self);
  if (PyErr_Occurred())
    return NULL;
  result = self->keyevents;
  if (result == NULL)
    result = PyList_New(0);
  else
    self->keyevents = NULL;
  return result;
}

static PyObject* display_mouseevents1(DisplayObject* self, PyObject* args)
{
  PyObject* result;
  ENABLE_EVENTS(ButtonPressMask);
  result = self->mouseevents;
  if (result == NULL)
    result = PyList_New(0);
  else
    self->mouseevents = NULL;
  return result;
}

static PyObject* display_pointermotion1(DisplayObject* self, PyObject* args)
{
  PyObject* result;
  ENABLE_EVENTS(PointerMotionMask);
  result = self->motionevent;
  if (result == NULL)
    {
      Py_INCREF(Py_None);
      result = Py_None;
    }
  else
    self->motionevent = NULL;
  return result;
}

static PyObject* display_flip1(DisplayObject* self, PyObject* args)
{
  int r;
  if (!checkopen(self))
    return NULL;

  r = paint_screen(self);
  if (!r)
  {
	  PyErr_SetString(PyExc_IOError, "cannot draw the screen");
	  return NULL;
  }

  flush(self);
  if (!readXevents(self))
    return NULL;
  Py_INCREF(Py_None);
  return Py_None;
}

static PyObject* display_shmmode(DisplayObject* self, PyObject *args)
{
  return PyLong_FromLong(0);
}

static PyObject* display_settitle(DisplayObject* self, PyObject* args)
{
  char* title;
  if (!checkopen(self))
    return NULL;
  if (!PyArg_ParseTuple(args, "s", &title))
    return NULL;
  SetWindowText(self->win, title);
  Py_INCREF(Py_None);
  return Py_None;
}

static PyMethodDef display_methods[] = {
  {"close",    (PyCFunction)display_close1,    METH_VARARGS,  NULL},
  {"flip",     (PyCFunction)display_flip1,     METH_VARARGS,  NULL},
  {"clear",    (PyCFunction)display_clear1,    METH_VARARGS,  NULL},
  {"pixmap",   (PyCFunction)display_pixmap1,   METH_VARARGS,  NULL},
  {"putppm",   (PyCFunction)display_putppm1,   METH_VARARGS,  NULL},
  {"getppm",   (PyCFunction)display_getppm1,   METH_VARARGS,  NULL},
  {"keyevents",(PyCFunction)display_keyevents1,METH_VARARGS,  NULL},
  {"mouseevents",(PyCFunction)display_mouseevents1,METH_VARARGS,NULL},
  {"pointermotion",(PyCFunction)display_pointermotion1,METH_VARARGS,NULL},
  {"shmmode",  (PyCFunction)display_shmmode,   METH_VARARGS,  NULL},
  {"settitle", (PyCFunction)display_settitle,  METH_VARARGS,  NULL},
  {NULL,		NULL}		/* sentinel */
};

/* The methods are found through tp_methods; Python 3 has no
   Py_FindMethod() for a tp_getattr function to use. */
static PyTypeObject Display_Type = {
	PyVarObject_HEAD_INIT(NULL, 0)
	.tp_name = "wingame.Display",
	.tp_basicsize = sizeof(DisplayObject),
	.tp_dealloc = (destructor)display_dealloc,
	.tp_flags = Py_TPFLAGS_DEFAULT,
	.tp_methods = display_methods,
};


 /************************** AUDIO PART ***************************/

#define NUM_WAVE_HDR    2

typedef struct {
	PyObject_HEAD
	HWAVEOUT waveOut;
	HANDLE doneEvent;
	WAVEHDR waveHdr[NUM_WAVE_HDR];
	int waveHdrCount, waveHdrNext;
} AudioObject;

#define AudioObject_Check(v)	(Py_TYPE(v) == &Audio_Type)
static PyTypeObject Audio_Type;


static PyObject* new_audio(PyObject* dummy, PyObject* args)
{
	WAVEFORMATEX wf;
	int channels, freq, bits, err, bufsize;
	AudioObject* self;
	if (!PyArg_ParseTuple(args, "iiii", &channels, &freq, &bits, &bufsize))
		return NULL;

	self = PyObject_New(AudioObject, &Audio_Type);
	if (self == NULL)
		return NULL;

	self->waveHdrCount = 0;
	self->waveHdrNext  = 0;
	self->waveOut      = 0;
	self->doneEvent    = CreateEvent(NULL, FALSE, TRUE, NULL);

	memset(&wf, 0, sizeof(wf));
	wf.wFormatTag      = WAVE_FORMAT_PCM;
	wf.nChannels       = channels;
	wf.nSamplesPerSec  = freq;
	wf.wBitsPerSample  = bits;
	wf.nBlockAlign     = wf.nChannels * wf.wBitsPerSample / 8;
	wf.nAvgBytesPerSec = wf.nSamplesPerSec * wf.nBlockAlign;
	err = waveOutOpen(&self->waveOut, WAVE_MAPPER, &wf, (DWORD_PTR) self->doneEvent, 0, CALLBACK_EVENT);
	if (err != MMSYSERR_NOERROR || self->doneEvent == NULL) {
		Py_DECREF(self);
		PyErr_SetString(PyExc_IOError, "cannot open audio device");
		return NULL;
	}

	while (self->waveHdrCount < NUM_WAVE_HDR) {
		WAVEHDR* wh = &self->waveHdr[self->waveHdrCount];
		wh->lpData         = PyMem_Malloc(bufsize);
		wh->dwBufferLength = bufsize;
		wh->dwFlags        = 0;
		if (wh->lpData == NULL || 
		    waveOutPrepareHeader(self->waveOut, wh, sizeof(WAVEHDR)) != MMSYSERR_NOERROR) {
			Py_DECREF(self);
			return NULL;
		}
		wh->dwFlags |= WHDR_DONE;
		self->waveHdrCount++;
	}
	return (PyObject*) self;
}

static void audio_close(AudioObject* self)
{
	if (self->waveOut != 0) {
		waveOutReset(self->waveOut);
		while (self->waveHdrCount > 0) {
			WAVEHDR* wh = &self->waveHdr[--self->waveHdrCount];
			waveOutUnprepareHeader(self->waveOut, wh, sizeof(WAVEHDR));
			PyMem_Free(wh->lpData);
		}
		waveOutClose(self->waveOut);
		self->waveOut = 0;
	}
}

static void audio_dealloc(AudioObject* self)
{
	audio_close(self);
	PyObject_Del(self);
}

static PyObject* audio_wait1(AudioObject* self, PyObject* args)
{
	float delay = -1.0;
	if (!PyArg_ParseTuple(args, "|f", &delay))
		return NULL;
	if (self->waveHdrNext >= self->waveHdrCount) {
		PyErr_SetString(PyExc_IOError, "audio device not ready");
		return NULL;
	}
	Py_BEGIN_ALLOW_THREADS
	while (!(self->waveHdr[self->waveHdrNext].dwFlags & WHDR_DONE)) {
		WaitForSingleObject(self->doneEvent, delay<0.0?INFINITE:(DWORD)(delay*1000.0));
	}
	Py_END_ALLOW_THREADS
	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject* audio_ready1(AudioObject* self, PyObject* args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	return PyLong_FromLong(self->waveHdrNext < self->waveHdrCount &&
			      (self->waveHdr[self->waveHdrNext].dwFlags & WHDR_DONE));
}

static PyObject* audio_write1(AudioObject* self, PyObject* args)
{
	WAVEHDR* wh;
	char* buffer;
	Py_ssize_t bufsize;
	if (!PyArg_ParseTuple(args, "s#", &buffer, &bufsize))
		return NULL;
	if (self->waveHdrNext >= self->waveHdrCount) {
		PyErr_SetString(PyExc_IOError, "audio device not ready");
		return NULL;
	}
	wh = &self->waveHdr[self->waveHdrNext];
	if (!(wh->dwFlags & WHDR_DONE)) {
		PyErr_SetString(PyExc_IOError, "audio device would block");
		return NULL;
	}
	if ((DWORD) bufsize != wh->dwBufferLength) {
		PyErr_SetString(PyExc_ValueError, "bufsize mismatch");
		return NULL;
	}
	wh->dwFlags &= ~WHDR_DONE;
	memcpy(wh->lpData, buffer, bufsize);
	if (waveOutWrite(self->waveOut, wh, sizeof(WAVEHDR)) != MMSYSERR_NOERROR) {
		PyErr_SetString(PyExc_IOError, "audio device write error");
		return NULL;
	}
	self->waveHdrNext++;
	if (self->waveHdrNext >= self->waveHdrCount)
		self->waveHdrNext = 0;

	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject* audio_close1(AudioObject* self, PyObject* args)
{
	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	audio_close(self);
	Py_INCREF(Py_None);
	return Py_None;
}


static PyMethodDef audio_methods[] = {
  {"ready",    (PyCFunction)audio_ready1,      METH_VARARGS,  NULL},
  {"wait",     (PyCFunction)audio_wait1,       METH_VARARGS,  NULL},
  {"write",    (PyCFunction)audio_write1,      METH_VARARGS,  NULL},
  {"close",    (PyCFunction)audio_close1,      METH_VARARGS,  NULL},
  {NULL,		NULL}		/* sentinel */
};

static PyTypeObject Audio_Type = {
	PyVarObject_HEAD_INIT(NULL, 0)
	.tp_name = "wingame.Audio",
	.tp_basicsize = sizeof(AudioObject),
	.tp_dealloc = (destructor)audio_dealloc,
	.tp_flags = Py_TPFLAGS_DEFAULT,
	.tp_methods = audio_methods,
};


static PyMethodDef WinMethods[] = {
           {"Display",  new_display,  METH_VARARGS},
           {"Audio",    new_audio,  METH_VARARGS},
           {NULL,       NULL}         /* Sentinel */
       };

static struct PyModuleDef wingamemodule = {
  PyModuleDef_HEAD_INIT, "wingame", NULL, -1, WinMethods
};

PyMODINIT_FUNC PyInit_wingame(void)
{
  if (PyType_Ready(&Display_Type) < 0 || PyType_Ready(&Audio_Type) < 0)
    return NULL;
  return PyModule_Create(&wingamemodule);
}
