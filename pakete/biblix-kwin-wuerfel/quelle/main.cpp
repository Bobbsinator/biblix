/*
    SPDX-FileCopyrightText: 2022 Vlad Zahorodnii <vlad.zahorodnii@kde.org>
    SPDX-License-Identifier: GPL-2.0-only OR GPL-3.0-only OR LicenseRef-KDE-Accepted-GPL
*/

#include "wuerfel.h"

namespace KWin
{

KWIN_EFFECT_FACTORY_SUPPORTED(WuerfelEffect, "metadata.json", return WuerfelEffect::supported();)

} // namespace KWin

#include "main.moc"
