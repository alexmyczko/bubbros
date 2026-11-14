# Relicensing permissions

The licence grants of the authors of The Bub's Brothers' graphics, sounds
and levels, kept as they arrived, so that anyone (Debian's ftp-masters
included) can check them.  The code is under the MIT License, see
LICENSE.txt.

| Author | Files | Licence | Status |
|---|---|---|---|
| David Gowers | the graphics he redrew in 2007 | Artistic-2.0 | granted 2026-11-12, below |
| Sebastian Wegner (McSebi) | Bub & Bob 1 graphics, sounds, music | Artistic (2005, LICENSE.txt) | confirmation asked 2026-11-12 |
| Sebastian Wegner (McSebi) | bubbob/levels/Levels.bin | not named in the 2005 grant | asked 2026-11-12 |
| Michael Repton | bubbob/levels/HouseOfFun.bin ("The House of Fun") | none recorded | no address; asked McSebi to forward |
| Wim De Gent | bubbob/levels/Arena.bin ("Bub & Bob Arena") | none recorded | no address; asked McSebi to forward |
| Patrick Viney | bubbob/levels/LostLevels.bin ("Lost Levels") | none recorded | no address; asked McSebi to forward |
| Armin Rigo, Gio, Michel-Stéphane | the Python levels (bubbob/levels/*.py) | MIT, like the code | confirmed 2026-11-14, below |
| unknown | the ext1 to ext7 sounds and music | none known | Armin has no record of their origin, below |

The three level packs were made by fans of the Mac game and published on
McSebi's site around 2002, credited to their authors
(https://web.archive.org/web/20020808194157/http://www.mcsebi.de:80/bb1.php).
They came with no licence, and McSebi's 2005 grant covers only "the
graphics and sound data" of his own game.

---

## Armin Rigo (2026-11-14)

**Key quotes:** *"Yes, the MIT licence applies to those levels too.  These two
are old friends of mine, credited because we made some of the levels
together."* and, about the ext1 to ext7 sounds, *"I have absolutely no
idea any more where the music came from."*

The message, as text.  The headers follow, without the X-Gm, X-Google and X-Pm
lines; the body arrived as plain text.  The mailbox (Proton)
stores the body encrypted with the recipient's key; it is shown here
decrypted.

```
From: Armin Rigo <armin.rigo@gmail.com>
Date: Sat, 14 Nov 2026 09:40:57 +0100
Subject: Re: The Bub's Brothers back in Debian GNU/Linux: copyright questions
To: Juan Manuel Méndez Rey <juan.mendezr@proton.me>

Hi Juan!

On Thu, 12 Nov 2026 at 22:39, Juan Manuel Méndez Rey
<juan.mendezr@proton.me> wrote:
> 1. The subgame sounds in bubbob/ext1 to ext7 (music.wav and brick, wall,
>    shoot, ouch, crash, fire, hit.wav). They are not from McSebi's
>    Bub & Bob. Where did they come from? The ext7 music was committed as
>    "Red Baron music".

I don't have any information any more; all I have is what is in the
CVS repo.  I have absolutely no idea any more where the music came
from.

> 2. Did David Gowers give a licence for his 2007 graphics?

As far as I know, yes.  Again, though, no idea about any detail and I
don't have my old e-mails any more.

> 3. Who are "Gio" and "Michel-Stéphane", credited for the Python levels,
>    and are those levels under the MIT licence of the code?

Yes, the MIT licence applies to those levels too.  These two are old
friends of mine, credited because we made some of the levels together.

> 4. Do you still have McSebi's 2005 permission mail? Alex lost his copy.

No, sorry.

Great to see that someone is trying to make that old project survive!
Sorry I can't help with that at all.

A bientôt,
Armin
```

<details>
<summary>Headers, as received (gmail.com DKIM signature, checked by Proton: dkim=pass)</summary>

```
Return-Path: <armin.rigo@gmail.com>
X-Original-To: juan.mendezr@proton.me
Delivered-To: juan.mendezr@proton.me
Received: from mail-lf1-f50.google.com (mail-lf1-f50.google.com [209.85.167.50]) (using
 TLSv1.3 with cipher TLS_AES_256_GCM_SHA384 (256/256 bits)
  key-exchange x25519 server-signature RSA-PSS (4096 bits) server-digest SHA512) (No
 client certificate requested) by mailinzur1016.protonmail.ch (Postfix) with ESMTPS id
 4jRSKC6Ysjz9vNPg for <juan.mendezr@proton.me>; Sat, 14 Nov 2026 08:41:35 +0000 (UTC)
Received: by mail-lf1-f50.google.com with SMTP id 2adb3069b0e04-5be3d5927ceso2641561e87.3
        for <juan.mendezr@proton.me>; Sat, 14 Nov 2026 00:41:35 -0800 (PST)
Authentication-Results: mail.protonmail.ch; dmarc=pass (p=none dis=none)
 header.from=gmail.com
Authentication-Results: mail.protonmail.ch; spf=pass smtp.mailfrom=gmail.com
Authentication-Results: mail.protonmail.ch; arc=pass smtp.remote-ip=209.85.167.50
 arc.chain=:google.com
Authentication-Results: mail.protonmail.ch; dkim=pass (2048-bit key) header.d=gmail.com
 header.i=@gmail.com header.b="WhJKq1VN"
Arc-Seal: i=1; a=rsa-sha256; t=1794645695; cv=none;
        d=google.com; s=arc-20260327;
        b=KjTAE/nxdff4rrGknVrRJU7+Uz6w5MigxXJqSnCDvUvNDuo/B+RUZXJEPThkGhS5Xl
         WZoJMJaSCvXdTUoQWUQGPjPVI808dLdEsSsp5bc3ZLisDBtKulHzV+pVDFIkJpmRoiB4
         WMD+Mug88UWZ36kUVLGi5paMg3cvPT7jX7MaWeTCYmSYtjA8htQkhRt1Ox+rZI5VR5Wp
         PS348QgtIhHJPfylArcOR+wK1TpmAafVsi0mqlyoT4LtYHrWsNPb0Z5B9yaGV7f3wkMJ
         IhofbXVzQORwglaDK7GWylkzutNvSXSpWaFY9PXhY95jCT5G1ucuhxuPeZmTnQxkLb+G
         u96g==
Arc-Message-Signature: i=1; a=rsa-sha256; c=relaxed/relaxed; d=google.com; s=arc-20260327;
        h=content-transfer-encoding:to:subject:message-id:date:from
         :in-reply-to:references:mime-version:dkim-signature;
        bh=Cp+J3XIsxhPe1wZcoSl+2gdtOUiGRBd5AZURNYZU/Dk=;
        fh=j+3xUHmlI9Tlm8/3ZAnlP0VWiJoHLRDPzoHQtm6Tnfg=;
        b=lqvpHgMSFhZCj5JsYH25RST6Tg95n2UVQHtllDcrlwI1RLMJ3GQANy/fO1b+g7Nm9c
         YZQY1it6B/oYW7fjQnjFQLYDHx5/CczBjm13TLeCTYty4QCsqyMtZoFnwHhdZSbIJ7bc
         wB7R6DjUnwxDOdO6dyGPV/dlPsgfbcSkqoNgeJz+74pVgeOJa1sHMabj4KdMbg0smTtT
         VjXjBItOsrflQ6gziFPAeSpiGUqEa8M8lSCAKb8nwzV/eWgAwfMit0ak6kxVnQ5TgFOV
         AiX3LLqmAGE/Onn6khLlBtVfppQeuYnkW9qj7JNEKD2UIMe24tB80HJH07gh2V3zgoU1
         4elQ==;
        darn=proton.me
Arc-Authentication-Results: i=1; mx.google.com; arc=none
Dkim-Signature: v=1; a=rsa-sha256; c=relaxed/relaxed;
        d=gmail.com; s=20260707; t=1794645695; x=1795250495; darn=proton.me;
        h=content-transfer-encoding:content-type:to:subject:message-id:date
         :from:in-reply-to:references:mime-version:from:to:cc:subject:date
         :message-id:reply-to:content-type;
        bh=Cp+J3XIsxhPe1wZcoSl+2gdtOUiGRBd5AZURNYZU/Dk=;
        b=WhJKq1VNeP+19DVilJZsdJHycF+wrmkGDTGiURFIQHs2pPhbaLfUDp2Z0FTTjVI99e
         5OtyWVf/F4HlwX3J5lAuAm9v21zsVVOzeE6q2PbxrLDhJnYCohKVu6xEYhpPWsVgsCXt
         kRodv3OOOMEpmZ9njnE0F19OEDhM2Ln6/OO6DEJspll2nWltDNdEG6mEteRYKpUEmx3s
         VYJzu/Avpb/KDMkp2rxKq2JyGx1QOpua1FGVyt3LFCGGCMLBWLMNeut4edKKYYVOgKeC
         B8W/M/5hO2dgECKT4uXBxdenVgjga2/q+XrQlxfn0pmTJhDVJLmXiOLcWykEqw3cQb0Z
         JGrw==
X-Received: by 2002:a05:6512:39d1:b0:5c1:5938:cbfd with SMTP id
 2adb3069b0e04-5c1709cf732mr2201420e87.56.1794645694859; Sat, 14 Nov 2026 00:41:34 -0800
 (PST)
Mime-Version: 1.0
References: <179451954297.269879.14590701938508704169@proton.me>
In-Reply-To: <179451954297.269879.14590701938508704169@proton.me>
From: Armin Rigo <armin.rigo@gmail.com>
Date: Sat, 14 Nov 2026 09:40:57 +0100
Message-Id: <CAMSv6X1-7rqN4UFkAgsALBvKKQijmCzvShX9x3KF5iQUJsef5A@mail.gmail.com>
Subject: Re: The Bub's Brothers back in Debian GNU/Linux: copyright questions
To: =?utf-8?Q?Juan_Manuel_M=C3=A9ndez_Rey?= <juan.mendezr@proton.me>
Content-Type: text/plain
Content-Transfer-Encoding: quoted-printable
```

</details>

---

## David Gowers (2026-11-12)

**Key quote:** *"Sure, I'm happy to release my updated graphics under
Artistic License 2.0."*

The message, as text.  It arrived as HTML only; the HTML body and the
headers follow, unedited.  The mailbox (Proton) stores the body encrypted
with the recipient's key; it is shown here decrypted.

```
From: David __ <finticemo@gmail.com>
Date: Fri, 13 Nov 2026 10:05:32 +1030
Subject: Re: Your Bub's Brothers graphics (2007) and Debian GNU/Linux
To: Juan Manuel Méndez Rey <juan.mendezr@proton.me>

Something I wasn't expecting to ever hear about again, TBH. Good to hear.

Sure, I'm happy to release my updated graphics under Artistic License
2.0. That should keep things simple.

If that's not quite explicit enough, let me know what else is required.

On Fri, Nov 13, 2026 at 8:09 AM Juan Manuel Méndez Rey
<juan.mendezr@proton.me> wrote:
> Hello David,
>
> In 2007 you redrew the graphics of The Bub's Brothers, Armin Rigo's free
> game. It now runs on Python 3 (https://github.com/alexmyczko/bubbros) and
> I am bringing it back into Debian GNU/Linux. Alex runs a public server,
> so you can play it over the Internet: start BubBob.py and choose
> "Internet games". The running games are listed at
> http://bubble.aiei.ch:8050/
>
> To fill in debian/copyright I need a licence for your graphics, and the
> game only credits you. Would you release them under the Artistic License
> 2.0, the licence of McSebi's originals they are based on? MIT or
> CC-BY-SA-4.0 would also work.
>
> A short reply that I may quote in the package and the upstream
> repository is all that is needed.
>
> Thank you,
>
> Juan Manuel Méndez Rey
```

<details>
<summary>Headers, as received (gmail.com DKIM signature, checked by Proton: dkim=pass)</summary>

```
Return-Path: <finticemo@gmail.com>
X-Original-To: juan.mendezr@proton.me
Delivered-To: juan.mendezr@proton.me
Received: from mail-lf1-f50.google.com (mail-lf1-f50.google.com [209.85.167.50]) (using
 TLSv1.3 with cipher TLS_AES_256_GCM_SHA384 (256/256 bits)
  key-exchange x25519 server-signature RSA-PSS (4096 bits) server-digest SHA512) (No
 client certificate requested) by mailinosl113.protonmail.ch (Postfix) with ESMTPS id
 4jQcFs44KPz5S for <juan.mendezr@proton.me>; Thu, 12 Nov 2026 23:35:45 +0000 (UTC)
Received: by mail-lf1-f50.google.com with SMTP id 2adb3069b0e04-5be416e603cso331819e87.2
        for <juan.mendezr@proton.me>; Thu, 12 Nov 2026 15:35:45 -0800 (PST)
Authentication-Results: mail.protonmail.ch; dmarc=pass (p=none dis=none)
 header.from=gmail.com
Authentication-Results: mail.protonmail.ch; spf=pass smtp.mailfrom=gmail.com
Authentication-Results: mail.protonmail.ch; arc=pass smtp.remote-ip=209.85.167.50
 arc.chain=:google.com
Authentication-Results: mail.protonmail.ch; dkim=pass (2048-bit key) header.d=gmail.com
 header.i=@gmail.com header.b="kJtL1d76"
Arc-Seal: i=1; a=rsa-sha256; t=1794526544; cv=none;
        d=google.com; s=arc-20260327;
        b=KRvjlRTignJyZYBzxnUbX8zkT0lJbRXapAd/cPpIjJ6xf00DY8GKXRvXShW0+7P30/
         TgYNyfdLPx7hSkJ30E0bo+tNtbNWZ4JzwZpDrvMxWi63rDExA/XyCy8h/ddiL28J8tQt
         l8RO7qOKgu+3KQsVoVpB2IH1Jp7rHmK9o3qiQK2drHoQ5P9HHhcfdrng6NPaywh8TvBI
         3S21JU+3szz/O4y9enDx/2/bzVBWoWEECHor5S1o1y+5WhU4vEMgwb0+JWqMs7FzueCc
         554/leQVuztIo/xArjLHi/Yw8mBrPCed4Y4aPH9X4T1mWXe/7peKYcfp4KohFCM8h8m5
         oVMw==
Arc-Message-Signature: i=1; a=rsa-sha256; c=relaxed/relaxed; d=google.com; s=arc-20260327;
        h=to:subject:message-id:date:from:in-reply-to:references:mime-version
         :dkim-signature;
        bh=6V+gX4kt+c/ulSft7ptg9Up/JUD3mVCny7PvGTzVrKM=;
        fh=j+3xUHmlI9Tlm8/3ZAnlP0VWiJoHLRDPzoHQtm6Tnfg=;
        b=lgAnT/UKsmK3s6z5PbicKfSuIEiPCvS+cvTYAZt3NFRowvY/FI1Xb+E+MYipD8XNh4
         j+TcRt4SdJrTDR28qBOX+6UN6FaqUZj5DGzWUzKtSEIshXWcXcv4xUefz8NjgFU4NhzT
         WaTzhnT0s5jDfeQIpg1Q+BIsffgIzmnU7E7N4mywKwyekpn/3Z3BiBPrtIREqerbOPaj
         uFuelQVVFS1iw+2jBgUoSO4OI+qex2cb3oqzMU0qcOTujMwmdSi9QQlD56oIAXrZs8rT
         pV2OqbWMUIU2xy+P0Yg9gXsZUjZ3rU3sdy+zxhWr6iHESFpE0UpLcHofBwrarDNuuTkW
         2+dQ==;
        darn=proton.me
Arc-Authentication-Results: i=1; mx.google.com; arc=none
Dkim-Signature: v=1; a=rsa-sha256; c=relaxed/relaxed;
        d=gmail.com; s=20260707; t=1794526544; x=1795131344; darn=proton.me;
        h=content-type:to:subject:message-id:date:from:in-reply-to:references
         :mime-version:from:to:cc:subject:date:message-id:reply-to
         :content-type;
        bh=6V+gX4kt+c/ulSft7ptg9Up/JUD3mVCny7PvGTzVrKM=;
        b=kJtL1d76lblTgjlrC/GTsCmh+wt0HVUxu839coL+OnsW4oDOyyLlzK+vZhrID3T+eA
         IOUuby8M0SchJcN3C8YdoG9w8eDF9S43SIeT2Rghm32VoxkZPAUHTn7e3mNVi2FdU6V9
         CwSgUnI7qQ6CpGO9soXU86ZihyfcsPA7UXscaUfcvDZz+mf3ATihqkRc3NTtoiG+VcHg
         IY8OYxnNv3Xmm6gVpTRTDjo9LRyNz+NfyuEwUOAM/ziaUohEvmqhZOyreDN3+4pZCBrN
         011At9Khki2Zzz+iLJz7+hhwQrg/nzqlAPzCYeYoNl+pK6KjG2jZK7XXaxjM9mXD/GPs
         beuw==
X-Google-Dkim-Signature: v=1; a=rsa-sha256; c=relaxed/relaxed;
        d=1e100.net; s=20260707; t=1794526544; x=1795131344;
        h=content-type:to:subject:message-id:date:from:in-reply-to:references
         :mime-version:x-gm-gg:x-gm-message-state:from:to:cc:subject:date
         :message-id:reply-to:content-type;
        bh=6V+gX4kt+c/ulSft7ptg9Up/JUD3mVCny7PvGTzVrKM=;
        b=VTlzRGZFrzA2V+sVvOOiIQ/nUVuSY5aidCqSqxEM8l7FU8xOwlAtP4DYLWc+BKgcfO
         ecF6VYK28zEamX09kJBnCdINZJ6J/urLXItH13Y61jnsMsTHUwFxDoPQ2aRlpWSqRcl0
         4Rl2LcQNQSQrQ9hr+X4FObzH+dY7HlHgHxzcSY5+UHUVjupFH6HmNhLnar2HkAPKTnVE
         VIghKZWGlp6lHeSKsjxtkO2q6g5zSivB9JAOLhjTU89eUpsd6osTRWBqhtJLT48uadNP
         /RKuHFPJDkhnaGy7TAHGkAhCtTlDxb8FePEueps5fF9gVzFO0ACHRr3xQ4fr7tnFpdPk
         fqZw==
X-Gm-Message-State: APuU4Z8ifg8TM+qiSGBEeE3i8V2Wsluj/362i9cgw8ZnzzQahopC6o96
 esL6IFLjNND4cRSk9GPmVTIzdGmapuofRvTCMVihD9L5H3WjcAUY6R2ae58IFjl2vkPSGW8yqdn
 kDIi195oYPq5uHN+jeBSH8ZfsSmucSDm0kw==
X-Gm-Gg: AYBFou0FoC9hxOKLRhHgfH0PAzfaTmo6R9JqrUd3FNmWhHwYyTJXYoGwN5dcGbri6ta
 rbOPoxmo+92F6tJYLc012BKEDx5wkcTNO0OkKUdP0U5WMRECoUXrsH4FlDGEekQftvQ78J7mZz+
 MnI35SMl4CFOjOtTV/tqKF5WKRvrWqF7zEzAehtU9milIzvoi0aPFUOSwdEHwtyeHaSnbteZB/z
 a1qtvyNY56xJtbpv+Jkodz85n60KvtMKTjDvvd0IzBOaCFRBsWgCcetUWxtGqIf17FkglnQG9ni
 P8yAFVBEqY8HZOtCnJBg0GSLXBiDx+JqvuwtTSrsvdENmce2ErRPFq3G6N1xFuOi9vBQ2sVqISQ
 EdG4y5qN+pJ595Q/t5QuC4CCAqlEdn8dQ/0j8pmyqXpzFTOlJehdRIq28/AO17ZxSGFvJMQ==
X-Received: by 2002:a05:6512:3d8a:b0:5c1:4e65:8ed0 with SMTP id
 2adb3069b0e04-5c170b51ed0mr331788e87.52.1794526544089; Thu, 12 Nov 2026 15:35:44 -0800
 (PST)
Mime-Version: 1.0
References: <179451954297.269879.14773028330989099348@proton.me>
In-Reply-To: <179451954297.269879.14773028330989099348@proton.me>
From: David __ <finticemo@gmail.com>
Date: Fri, 13 Nov 2026 10:05:32 +1030
X-Gm-Features: AclHuK-r36QYFaH0synuZit5eiElYKb7Tgvn1VoPVLxmG5i34Uojh50HiLClHLc
Message-Id: <CAMf8R05As6QS7_dJVcvd3kNEh08RUi7=-ihtpzqZ7SUnQXifvA@mail.gmail.com>
Subject: Re: Your Bub's Brothers graphics (2007) and Debian GNU/Linux
To: =?utf-8?Q?Juan_Manuel_M=C3=A9ndez_Rey?= <juan.mendezr@proton.me>
Content-Type: text/html
X-Pm-Spam: 0yezJI6YSpyJec91ztFGcjIwoJyLCvXBZcQniisnOERJt9TTVOUdSRQUiwslOjLdFJEL
 CN0lSXZ1BElETjIbpAuLTsV0MIRkLf1USkVMFRfSUiVUQOsltx4CMSXiwtJREWV9TQxUJF9FRiR6I0
 wWydjFLLJCGFVkUUTJF9GTFNk9UIpjbiwCMmZulljdGvW1ZWF20tdWXWYslNvLmdSJbLJCIM1EV0XF
 1NBU1i0UROslwiwSXVTHNRfSUPlJRT9VNfFEVESBVVSREbjpIM0FsDJlIkVfR5fSUQVNTStUFyg0Xj
 IbpwiMC5jAMLgj12EjLyN14BsMC0XNaZQWgg4Wa2duwFpbWwHNbatWll5mLCddJJTLCfEZUSVEMO91
 T0TF5pbIjsF0MINlQQ9lRVQTNpbIjdTBLLJCXSlURFRQ9JUT1bjpIM1F9zJCL2Yy9I6ZSiCwMcN2vk
 VmcjIto4yMCiSwfcI3iisnOWY0N9uaWijoIa5Wiig3bCLtJ9zbFy29YZIS6QJyekUE9otIjsjUMIBl
 SfR0TFUFJlDREPElVTIi6iwCMlUiM01OiTCJLQIS6uATLiMiwRlX2nnVYXl2ui8mZnOisJPUF6CIRe
 JypnFWbVZu91lYWijoIaNH0rNWY2XpZVfbmuHVdZRWffVHcjMyAEwNjijgMLJCtslWYzXwN9tcll2R
 bbIC6h1mIWazwItcHwTILMYjwxETNnL0BwiIipWFbb8FzfJHcHcvJI6YiiCwMbFWplRHbHefR1iZWk
 WRZa5Wnv12XGZsVoiIj0W5aZxmvvQXYXbsVlsdGnW5adFWs1UWLXLtNxsYWiiwIc9FztFGcjIwoAwL
 j2zQNNEzw5MDMjN1cM1MjszUNIBnfhB3cVbi9NlYXwjoILAjw2QzNzNwEM5MD1jcNMMj1sUzNnIfBd
 pc3oGNdXR3voB3XXaoN5naWwjoILAjw1YDMjM1EU0MDwjAMOYTyskTMnI1J9ubllW1YIoji0F2d2Ys
 hN0aXlXNLbRmlw1icVdz9l0d2i2gYf1X9zJCLmckloiIjmmFNNRjkxMTNWY1UZjNTiWJYMQz0kVGNn I91
X-Pm-Origin: external
X-Pm-Transfer-Encryption: TLSv1.3 with cipher TLS_AES_256_GCM_SHA384 (256/256 bits)
X-Pm-Content-Encryption: on-delivery
X-Pm-Spamscore: 0
X-Pm-Spam-Action: inbox
```

</details>

<details>
<summary>Body, as received (text/html)</summary>

```html
<div dir="ltr"><div>Something I wasn&#39;t expecting to ever hear about again, TBH. Good to hear.</div><div><br></div><div>Sure, I&#39;m happy to release my updated graphics under Artistic License 2.0. That should keep things simple.</div><div><br></div><div>If that&#39;s not quite explicit enough, let me know what else is required.</div><div><br></div><div><br></div></div><br><div class="gmail_quote gmail_quote_container"><div dir="ltr" class="gmail_attr">On Fri, Nov 13, 2026 at 8:09 AM Juan Manuel Méndez Rey &lt;<a href="mailto:juan.mendezr@proton.me">juan.mendezr@proton.me</a>&gt; wrote:<br></div><blockquote class="gmail_quote" style="margin:0px 0px 0px 0.8ex;border-left:1px solid rgb(204,204,204);padding-left:1ex">Hello David,<br>
<br>
In 2007 you redrew the graphics of The Bub&#39;s Brothers, Armin Rigo&#39;s free<br>
game. It now runs on Python 3 (<a href="https://github.com/alexmyczko/bubbros" rel="noreferrer" target="_blank">https://github.com/alexmyczko/bubbros</a>) and<br>
I am bringing it back into Debian GNU/Linux. Alex runs a public server,<br>
so you can play it over the Internet: start BubBob.py and choose<br>
&quot;Internet games&quot;. The running games are listed at<br>
<a href="http://bubble.aiei.ch:8050/" rel="noreferrer" target="_blank">http://bubble.aiei.ch:8050/</a><br>
<br>
To fill in debian/copyright I need a licence for your graphics, and the<br>
game only credits you. Would you release them under the Artistic License<br>
2.0, the licence of McSebi&#39;s originals they are based on? MIT or<br>
CC-BY-SA-4.0 would also work.<br>
<br>
A short reply that I may quote in the package and the upstream<br>
repository is all that is needed.<br>
<br>
Thank you,<br>
<br>
Juan Manuel Méndez Rey<br>
<br>
</blockquote></div>
```

</details>
