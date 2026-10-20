# Biblix: Hardware-Videodekodierung mit NVIDIA (nvidia-vaapi-driver).
# Nur wenn der NVIDIA-Treiber laeuft; AMD/Intel waehlen ihren Treiber selbst.
if [ -e /sys/module/nvidia_drm ]; then
    export LIBVA_DRIVER_NAME=nvidia
    export NVD_BACKEND=direct
    # Firefox braucht das fuer nvidia-vaapi-driver
    export MOZ_DISABLE_RDD_SANDBOX=1
fi
