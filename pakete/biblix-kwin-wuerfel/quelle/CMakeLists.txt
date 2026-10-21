cmake_minimum_required(VERSION 3.16)
project(biblix-kwin-wuerfel)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(ECM 6.0 REQUIRED NO_MODULE)
set(CMAKE_MODULE_PATH ${CMAKE_MODULE_PATH} ${ECM_MODULE_PATH})
include(KDEInstallDirs)
include(KDECMakeSettings)
include(KDECompilerSettings NO_POLICY_SCOPE)

find_package(Qt6 6.7 REQUIRED COMPONENTS Core Gui Quick)
find_package(KF6 6.10 REQUIRED COMPONENTS Config CoreAddons GlobalAccel I18n WindowSystem)
find_package(KWin REQUIRED)

kcoreaddons_add_plugin(biblix_wuerfel INSTALL_NAMESPACE "kwin/effects/plugins/")
target_sources(biblix_wuerfel PRIVATE wuerfel.cpp main.cpp)
kconfig_add_kcfg_files(biblix_wuerfel wuerfelconfig.kcfgc)
target_link_libraries(biblix_wuerfel
    Qt6::Core Qt6::Gui Qt6::Quick
    KF6::ConfigCore KF6::ConfigGui KF6::CoreAddons KF6::GlobalAccel KF6::I18n
    KWin::kwin)

install(DIRECTORY qml DESTINATION ${KDE_INSTALL_DATADIR}/kwin/effects/biblix_wuerfel)
