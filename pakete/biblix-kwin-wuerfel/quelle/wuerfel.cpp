/*
    Biblix-Würfel (siehe wuerfel.h)
    SPDX-License-Identifier: GPL-2.0-only OR GPL-3.0-only OR LicenseRef-KDE-Accepted-GPL
*/

#include "wuerfel.h"
#include "wuerfelconfig.h"

#include <core/output.h>
#include <effect/effecthandler.h>
#include <virtualdesktops.h>

#include <QAction>
#include <QQuickItem>
#include <QStandardPaths>
#include <QTimer>

#include <KGlobalAccel>
#include <KLocalizedString>

#include <utility>

using namespace std::chrono_literals;

namespace KWin
{

WuerfelEffect::WuerfelEffect()
    : m_shutdownTimer(new QTimer(this))
{
    qmlRegisterUncreatableType<WuerfelEffect>("de.biblix.wuerfel", 1, 0, "WuerfelEffect", QStringLiteral("nur in KWin"));

    m_shutdownTimer->setSingleShot(true);
    connect(m_shutdownTimer, &QTimer::timeout, this, &WuerfelEffect::realDeactivate);
    connect(effects, &EffectsHandler::screenAboutToLock, this, &WuerfelEffect::realDeactivate);
    connect(effects, &EffectsHandler::desktopChanged, this,
            [this](VirtualDesktop *alt, VirtualDesktop *neu, EffectWindow *) {
                arbeitsflaecheGewechselt(alt, neu);
            });

    const QKeySequence standard = Qt::META | Qt::Key_C;
    m_toggleAction = new QAction(this);
    m_toggleAction->setObjectName(QStringLiteral("BiblixWuerfel"));
    m_toggleAction->setText(i18n("Biblix-Würfel ein/aus"));
    KGlobalAccel::self()->setDefaultShortcut(m_toggleAction, {standard});
    KGlobalAccel::self()->setShortcut(m_toggleAction, {standard});
    m_toggleShortcut = KGlobalAccel::self()->shortcut(m_toggleAction);
    connect(m_toggleAction, &QAction::triggered, this, &WuerfelEffect::toggle);

    setSource(QUrl::fromLocalFile(QStandardPaths::locate(QStandardPaths::GenericDataLocation,
                                                         QStringLiteral("kwin/effects/biblix_wuerfel/qml/main.qml"))));
    reconfigure(ReconfigureAll);
}

void WuerfelEffect::reconfigure(ReconfigureFlags)
{
    WuerfelConfig::self()->read();
    const int dauer = animationTime(std::chrono::milliseconds(WuerfelConfig::dauer()));
    if (dauer != m_animationDuration) {
        m_animationDuration = dauer;
        Q_EMIT animationDurationChanged();
    }
    m_cubeFaceDisplacement = WuerfelConfig::flaechenAbstand();
    m_distanceFactor = WuerfelConfig::entfernung() / 100.0;
    m_backgroundColor = WuerfelConfig::hintergrundfarbe();
}

void WuerfelEffect::arbeitsflaecheGewechselt(VirtualDesktop *alt, VirtualDesktop *neu)
{
    // Nur als Übergang, wenn nichts anderes läuft (kein Vollbild-Spiel, kein Sperrbildschirm, keine Übersicht)
    if (isRunning() || !alt || !neu || alt == neu) {
        return;
    }
    if (effects->isScreenLocked() || effects->hasActiveFullScreenEffect() || effects->desktops().count() < 2) {
        return;
    }
    if (m_animationDuration <= 1) {
        return;
    }
    m_uebergang = true;
    m_von = alt;
    m_nach = neu;
    setRunning(true);
}

QVariantMap WuerfelEffect::initialProperties(Output *screen)
{
    return QVariantMap{
        {QStringLiteral("effect"), QVariant::fromValue(this)},
        {QStringLiteral("targetScreen"), QVariant::fromValue(screen)},
        {QStringLiteral("uebergang"), m_uebergang},
        {QStringLiteral("vonDesktop"), QVariant::fromValue(static_cast<QObject *>(m_von.data()))},
        {QStringLiteral("nachDesktop"), QVariant::fromValue(static_cast<QObject *>(m_nach.data()))},
    };
}

int WuerfelEffect::requestedEffectChainPosition() const
{
    return 70;
}

void WuerfelEffect::grabbedKeyboardEvent(QKeyEvent *e)
{
    if (e->type() == QEvent::KeyPress && m_toggleShortcut.contains(e->key() | e->modifiers())) {
        toggle();
        return;
    }
    QuickSceneEffect::grabbedKeyboardEvent(e);
}

void WuerfelEffect::toggle()
{
    if (isRunning()) {
        deactivate();
    } else {
        activate();
    }
}

void WuerfelEffect::activate()
{
    if (effects->isScreenLocked() || effects->desktops().count() < 2) {
        return;
    }
    m_uebergang = false;
    setRunning(true);
}

void WuerfelEffect::deactivate()
{
    if (m_shutdownTimer->isActive()) {
        return;
    }
    const QList<Output *> screens = effects->screens();
    for (Output *screen : screens) {
        if (QuickSceneView *view = viewForScreen(screen)) {
            QMetaObject::invokeMethod(view->rootItem(), "stop");
        }
    }
    m_shutdownTimer->start(m_animationDuration);
}

void WuerfelEffect::realDeactivate()
{
    m_uebergang = false;
    setRunning(false);
}

int WuerfelEffect::animationDuration() const
{
    return m_animationDuration;
}

qreal WuerfelEffect::cubeFaceDisplacement() const
{
    return m_cubeFaceDisplacement;
}

qreal WuerfelEffect::distanceFactor() const
{
    return m_distanceFactor;
}

QColor WuerfelEffect::backgroundColor() const
{
    return m_backgroundColor;
}

} // namespace KWin
