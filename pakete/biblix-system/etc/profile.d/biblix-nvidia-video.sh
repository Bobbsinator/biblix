# Biblix: Hardware-Videodekodierung mit NVIDIA (nvidia-vaapi-driver).
# Nur wenn der NVIDIA-Treiber laeuft; AMD/Intel waehlen ihren Treiber selbst.
if [ -e /sys/module/nvidia_drm ]; then
    export LIBVA_DRIVER_NAME=nvidia
    export NVD_BACKEND=direct
    # MOZ_DISABLE_RDD_SANDBOX setzt nur der Bibi Browser selbst (nicht systemweit, Sicherheit)
fi
