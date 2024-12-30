#!/bin/bash

export EXT_MODULES="
    external/sm8450-modules/qcom/opensource/mmrm-driver
    external/sm8450-modules/qcom/opensource/audio-kernel
    external/sm8450-modules/qcom/opensource/camera-kernel
    external/sm8450-modules/qcom/opensource/display-drivers/msm
    external/sm8450-modules/qcom/opensource/cvp-kernel \
    external/sm8450-modules/qcom/opensource/dataipa/drivers/platform/msm \
    external/sm8450-modules/qcom/opensource/datarmnet/core \
    external/sm8450-modules/qcom/opensource/datarmnet-ext/aps \
    external/sm8450-modules/qcom/opensource/datarmnet-ext/offload \
    external/sm8450-modules/qcom/opensource/datarmnet-ext/shs \
    external/sm8450-modules/qcom/opensource/datarmnet-ext/perf \
    external/sm8450-modules/qcom/opensource/datarmnet-ext/perf_tether \
    external/sm8450-modules/qcom/opensource/datarmnet-ext/sch \
    external/sm8450-modules/qcom/opensource/datarmnet-ext/wlan \
    external/sm8450-modules/qcom/opensource/eva-kernel \
    external/sm8450-modules/qcom/opensource/video-driver \
    external/sm8450-modules/cirrus/kernel-modules/cs35l41/sound/soc/codecs \
    external/sm8450-modules/cirrus/kernel-modules/cs40l25/drivers/misc \
    external/sm8450-modules/cirrus/kernel-modules/cs40l25/sound/soc/codecs \
    external/sm8450-modules/semc/hardware/camera-kernel-module/camera_sync \
    external/sm8450-modules/semc/hardware/camera-kernel-module/sony_camera \
    external/sm8450-modules/semc/hardware/camera-kernel-module/tcs3490 \
    external/sm8450-modules/semc/hardware/camera-kernel-module/slg51000_regulator \
    external/sm8450-modules/semc/hardware/charge/kernel-modules/battman_dbg \
    external/sm8450-modules/semc/hardware/charge/kernel-modules/battchg_ext \
    external/sm8450-modules/semc/hardware/kernel-modules/misc/bu520x1nvx \
    external/sm8450-modules/semc/hardware/kernel-modules/misc/et6xx \
    external/sm8450-modules/semc/hardware/kernel-modules/misc/last_logs \
    external/sm8450-modules/semc/hardware/kernel-modules/misc/ldo_vibrator \
    external/sm8450-modules/semc/hardware/kernel-modules/misc/powerkey_forcecrash \
    external/sm8450-modules/semc/hardware/kernel-modules/msm/sec_ts \
    external/sm8450-modules/semc/hardware/nfc/drivers/sn1x0_i2c \
    external/sm8450-modules/semc/hardware/nfc/drivers/sn1x0_spi
"
# worked before with this on top: external/kernel/kernel-modules/mmrm-driver 

excluded="
    
    external/sm8450-modules/qcom/opensource/wlan/qcacld-3.0/.qca6490 \
"

# export SKIP_MRPROPER=1
# export SKIP_DEFCONFIG=1

export BUILD_CONFIG=external/kernel/build.config.msm.waipio
export VARIANT=gki
#export VARIANT=consolidate
export LTO=thin

echo Building with external modules
echo $EXT_MODULES
echo

build/build.sh

# strip all modules
find out/msm-waipio-waipio*/dist/ -iname "*.ko" -exec ./prebuilts-master/clang/host/linux-x86/clang-r399163b/bin/llvm-strip --strip-debug {} \;
