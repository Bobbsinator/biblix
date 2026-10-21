/*
    Biblix-Würfel: 3D-Würfel beim Wechsel der Arbeitsfläche (und mit Meta+C zum Drehen per Maus).

    Portiert und erweitert von kwin-effects-cube (Vlad Zahorodnii) für KWin 6.3.
    SPDX-FileCopyrightText: 2022 Vlad Zahorodnii <vlad.zahorodnii@kde.org>
    SPDX-FileCopyrightText: 2026 Biblix
    SPDX-License-Identifier: GPL-2.0-only OR GPL-3.0-only OR LicenseRef-KDE-Accepted-GPL
*/

#pragma once

#include <effect/quickeffect.h>

#include <QAction>
#include <QKeySequence>
#include <QPointer>
#include <QTimer>

namespace KWin
{

class VirtualDesktop;

class WuerfelEffect : public QuickSceneEffect
{
    Q_OBJECT
    Q_PROPERTY(int animationDuration READ animationDuration NOTIFY animationDurationChanged)
    Q_PROPERTY(qreal cubeFaceDisplacement READ cubeFaceDisplacement CONSTANT)
    Q_PROPERTY(qreal distanceFactor READ distanceFactor CONSTANT)
    Q_PROPERTY(QColor backgroundColor READ backgroundColor CONSTANT)

public:
    WuerfelEffect();

    void reconfigure(ReconfigureFlags flags) override;
    int requestedEffectChainPosition() const override;
    void grabbedKeyboardEvent(QKeyEvent *e) override;

    int animationDuration() const;
    qreal cubeFaceDisplacement() const;
    qreal distanceFactor() const;
    QColor backgroundColor() const;

public Q_SLOTS:
    void activate();
    void deactivate();
    void toggle();

Q_SIGNALS:
    void animationDurationChanged();

protected:
    QVariantMap initialProperties(Output *screen) override;

private:
    void realDeactivate();
    void arbeitsflaecheGewechselt(VirtualDesktop *alt, VirtualDesktop *neu);

    QTimer *m_shutdownTimer;
    QAction *m_toggleAction = nullptr;
    QList<QKeySequence> m_toggleShortcut;
    qreal m_cubeFaceDisplacement = 100;
    qreal m_distanceFactor = 1.5;
    QColor m_backgroundColor;
    int m_animationDuration = 200;

    bool m_uebergang = false;
    QPointer<VirtualDesktop> m_von;
    QPointer<VirtualDesktop> m_nach;
};

} // namespace KWin
