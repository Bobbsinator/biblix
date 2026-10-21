/*
    Biblix-Würfel: Szene.
    Übergang (uebergang = true): kurz herauszoomen, zur neuen Arbeitsfläche drehen, wieder heranzoomen.
    Interaktiv (Meta+C): wie kwin-effects-cube, mit Maus drehen und Fläche wählen.

    SPDX-FileCopyrightText: 2022 Vlad Zahorodnii <vlad.zahorodnii@kde.org>
    SPDX-FileCopyrightText: 2026 Biblix
    SPDX-License-Identifier: GPL-2.0-only OR GPL-3.0-only OR LicenseRef-KDE-Accepted-GPL
*/

import QtQuick
import QtQuick3D
import org.kde.kwin as KWinComponents

Item {
    id: root
    focus: true

    required property QtObject effect
    required property QtObject targetScreen
    property bool uebergang: false
    property QtObject vonDesktop: null
    property QtObject nachDesktop: null

    property bool animationEnabled: false

    function start() {
        if (root.uebergang && root.vonDesktop && root.nachDesktop) {
            cameraController.rotation = Quaternion.fromEulerAngles(0, cube.desktopAzimuth(root.vonDesktop), 0);
            cameraController.radius = cameraController.nahRadius;
            uebergangAnimation.start();
            return;
        }
        cameraController.rotateTo(KWinComponents.Workspace.currentDesktop);
        root.animationEnabled = true;
        cameraController.state = "distant";
    }

    function stop() {
        if (root.uebergang) {
            return;
        }
        cameraController.rotateTo(KWinComponents.Workspace.currentDesktop);
        cameraController.state = "close";
    }

    function switchToSelected() {
        if (root.uebergang) {
            return;
        }
        const eulerRotation = cameraController.rotation.toEulerAngles();
        KWinComponents.Workspace.currentDesktop = cube.desktopAt(eulerRotation.y);
        effect.deactivate();
    }

    // kürzester Weg zwischen zwei Winkeln
    function zielWinkel(von, nach) {
        let d = (nach - von) % 360;
        if (d > 180) d -= 360;
        if (d < -180) d += 360;
        return von + d;
    }

    SequentialAnimation {
        id: uebergangAnimation
        property real von: root.vonDesktop ? cube.desktopAzimuth(root.vonDesktop) : 0
        property real nach: root.nachDesktop ? root.zielWinkel(von, cube.desktopAzimuth(root.nachDesktop)) : 0
        NumberAnimation {
            target: cameraController; property: "radius"
            to: cameraController.fernRadius
            duration: root.effect.animationDuration * 0.45
            easing.type: Easing.OutCubic
        }
        NumberAnimation {
            target: cameraController; property: "azimut"
            from: uebergangAnimation.von; to: uebergangAnimation.nach
            duration: root.effect.animationDuration
            easing.type: Easing.InOutCubic
        }
        NumberAnimation {
            target: cameraController; property: "radius"
            to: cameraController.nahRadius
            duration: root.effect.animationDuration * 0.45
            easing.type: Easing.OutBack
            easing.overshoot: 1.2
        }
        ScriptAction { script: root.effect.deactivate() }
    }

    View3D {
        id: view
        anchors.fill: parent

        environment: SceneEnvironment {
            clearColor: root.effect.backgroundColor
            backgroundMode: SceneEnvironment.Color
        }

        PerspectiveCamera { id: camera }

        Cube {
            id: cube
            faceDisplacement: root.effect.cubeFaceDisplacement
            faceSize: Qt.size(root.width, root.height)
        }

        CubeCameraController {
            id: cameraController
            anchors.fill: parent
            state: root.uebergang ? "" : "close"
            camera: camera
            enabled: !root.uebergang

            readonly property real nahRadius: cube.faceDistance + 0.5 * cube.faceSize.height / Math.tan(0.5 * camera.fieldOfView * Math.PI / 180)
            readonly property real fernRadius: cube.faceDistance * root.effect.distanceFactor + 0.5 * cube.faceSize.height / Math.tan(0.5 * camera.fieldOfView * Math.PI / 180)
            // Drehwinkel für den Übergang
            property real azimut: 0
            onAzimutChanged: if (root.uebergang) rotation = Quaternion.fromEulerAngles(0, azimut, 0)

            states: [
                State {
                    name: "close"
                    PropertyChanges { target: cameraController; radius: cameraController.nahRadius }
                },
                State {
                    name: "distant"
                    PropertyChanges { target: cameraController; radius: cameraController.fernRadius }
                }
            ]

            Behavior on rotation {
                enabled: !cameraController.busy && root.animationEnabled && !root.uebergang
                QuaternionAnimation {
                    id: rotationAnimation
                    duration: root.effect.animationDuration
                    easing.type: Easing.OutCubic
                }
            }
            Behavior on radius {
                enabled: !root.uebergang
                NumberAnimation {
                    duration: root.effect.animationDuration
                    easing.type: Easing.OutCubic
                }
            }

            function rotateToLeft() {
                if (!rotationAnimation.running) {
                    rotation = Quaternion.fromEulerAngles(0, -cube.angleTick, 0).times(rotation);
                }
            }
            function rotateToRight() {
                if (!rotationAnimation.running) {
                    rotation = Quaternion.fromEulerAngles(0, cube.angleTick, 0).times(rotation);
                }
            }
            function rotateTo(desktop) {
                if (!rotationAnimation.running) {
                    rotation = Quaternion.fromEulerAngles(0, cube.desktopAzimuth(desktop), 0);
                }
            }
        }
    }

    MouseArea {
        anchors.fill: view
        enabled: !root.uebergang
        onClicked: root.switchToSelected()
    }

    Keys.onEscapePressed: if (!root.uebergang) root.effect.deactivate()
    Keys.onLeftPressed: cameraController.rotateToLeft()
    Keys.onRightPressed: cameraController.rotateToRight()
    Keys.onEnterPressed: root.switchToSelected()
    Keys.onReturnPressed: root.switchToSelected()
    Keys.onSpacePressed: root.switchToSelected()

    Component.onCompleted: start()
}
