#!/bin/bash

# Script to build stock kernel with external modules from Lineage sm8450-modules
# To use: 
#  - setup environment as for GKI https://source.android.com/docs/setup/build/building-kernels
#  - add Sony kernel (kernel-copyleft) and modules to it. Below, /android/external/kernel and /android/external/sm8450-modules were used
#    Note that modules have to be in sm8450-modules folder
#  - adjust CLANG path as needed
#  - run this script



# Directory setup
KERNEL_DIR="/android/external/kernel"
BUILD_ROOT="/android/out/kernel"

# Set up LLVM toolchain path
CLANG_PATH="/android/prebuilts-master/clang/host/linux-x86/clang-r416183b"
TOOLS_PATH="/android/prebuilts/kernel-build-tools/linux-x86"

EXT_MODULES="
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
    external/sm8450-modules/qcom/opensource/wlan/qcacld-3.0/.qca6490 \
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
    external/sm8450-modules/semc/hardware/kernel-modules/misc/rdtags \
    external/sm8450-modules/semc/hardware/kernel-modules/msm/sec_ts \
    external/sm8450-modules/semc/hardware/nfc/drivers/sn1x0_i2c \
    external/sm8450-modules/semc/hardware/nfc/drivers/sn1x0_spi
"

set -e

# Set up build environment variables
export ARCH=arm64
export CROSS_COMPILE=aarch64-linux-gnu-
export CROSS_COMPILE_ARM32=arm-linux-gnueabi-
export LLVM=1
export LLVM_IAS=1
export LTO=thin  # Set default LTO mode
export PATH="$CLANG_PATH/bin:$TOOLS_PATH/bin:$PATH"

# directories used in the build
BUILD_DIR="$BUILD_ROOT/build"
DIST_DIR="$BUILD_ROOT/dist"
MODULE_DIR="${DIST_DIR}/modules"

# Clean build directory
rm -rf $BUILD_ROOT
mkdir -p $BUILD_DIR
mkdir -p $DIST_DIR
mkdir -p $MODULE_DIR

# Configuration steps
cd $KERNEL_DIR

# 1. First, copy the default config
echo "Preparing kernel config..."
make O=$BUILD_DIR V=1 gki_defconfig

# 2. Merge with vendor config
echo "Merging vendor config..."
scripts/kconfig/merge_config.sh -O $BUILD_DIR \
    arch/arm64/configs/gki_defconfig \
    arch/arm64/configs/vendor/waipio_GKI.config \
    arch/arm64/configs/vendor/sony/nagara.config \
    arch/arm64/configs/vendor/sony/pdx223.config

# Configure LTO
echo "========================================================"
echo " Modifying LTO mode to '${LTO}'"
echo "========================================================"

if [ "${LTO}" = "none" -o "${LTO}" = "thin" -o "${LTO}" = "full" ]; then
    if [ "${LTO}" = "none" ]; then
        ${KERNEL_DIR}/scripts/config --file ${BUILD_DIR}/.config \
            -d LTO_CLANG \
            -e LTO_NONE \
            -d LTO_CLANG_THIN \
            -d LTO_CLANG_FULL \
            -d THINLTO
    elif [ "${LTO}" = "thin" ]; then
        ${KERNEL_DIR}/scripts/config --file ${BUILD_DIR}/.config \
            -e LTO_CLANG \
            -d LTO_NONE \
            -e LTO_CLANG_THIN \
            -d LTO_CLANG_FULL \
            -e THINLTO
    elif [ "${LTO}" = "full" ]; then
        ${KERNEL_DIR}/scripts/config --file ${BUILD_DIR}/.config \
            -e LTO_CLANG \
            -d LTO_NONE \
            -d LTO_CLANG_THIN \
            -e LTO_CLANG_FULL \
            -d THINLTO
    fi
else
    echo "LTO= must be one of 'none', 'thin' or 'full'."
    exit 1
fi

# Build flags
KBUILD_OPTIONS="
    O=$BUILD_DIR \
    ARCH=arm64 \
    CC=clang \
    LD=ld.lld \
    AR=llvm-ar \
    NM=llvm-nm \
    OBJCOPY=llvm-objcopy \
    OBJDUMP=llvm-objdump \
    STRIP=llvm-strip \
    LLVM=1 \
    LLVM_IAS=1"

# Prepare for build
cd $BUILD_DIR

# Update config after LTO changes
echo "Updating config..."
make $KBUILD_OPTIONS olddefconfig

# Build kernel
echo "Building kernel..."
make $KBUILD_OPTIONS -j$(nproc)

# Get kernel release version
KERNEL_RELEASE=$(cat $BUILD_DIR/include/config/kernel.release)

# Build and organize modules
echo "Building and installing modules..."
TEMP_MOD_DIR=$(mktemp -d)
make $KBUILD_OPTIONS modules_install INSTALL_MOD_PATH=$TEMP_MOD_DIR

# Build external modules if EXT_MODULES is set
if [ ! -z "${EXT_MODULES}" ]; then
    echo "Building external modules..."
    for EXT_MOD in ${EXT_MODULES}; do
        MDIR="/android/${EXT_MOD}"
        if [ -d ${MDIR} ]; then
            echo "Building ${EXT_MOD}..."          
            pushd ${MDIR}
            RELATIVE_PATH=$(realpath --no-symlinks --relative-to="$KERNEL_DIR" "$MDIR")
            make KERNEL_SRC=$KERNEL_DIR OUT_DIR=$BUILD_DIR $KBUILD_OPTIONS M=${RELATIVE_PATH}
            make KERNEL_SRC=$KERNEL_DIR OUT_DIR=$BUILD_DIR $KBUILD_OPTIONS M=${RELATIVE_PATH} modules_install INSTALL_MOD_PATH=$TEMP_MOD_DIR
            popd
        else
            echo "Warning: External module directory not found: ${EXT_MOD}"
        fi
    done
fi

# Strip modules
echo "Stripping modules..."
find $TEMP_MOD_DIR -name "*.ko" -exec llvm-strip --strip-debug {} \;

# Copy all modules to the flat directory
echo "Creating flat module directory..."
find $TEMP_MOD_DIR -name "*.ko" -exec cp {} $MODULE_DIR \;
find $TEMP_MOD_DIR -name "modules.*" -exec cp {} $MODULE_DIR \;

# Create temporary directory for depmod
DEPMOD_DIR=$(mktemp -d)
DEPMOD_MOD_DIR="${DEPMOD_DIR}/lib/modules/${KERNEL_RELEASE}"
mkdir -p "${DEPMOD_MOD_DIR}"

# Copy modules to depmod directory
cp $MODULE_DIR/* "${DEPMOD_MOD_DIR}/"

# Copy modules.builtin* files from build directory
cp $BUILD_DIR/modules.builtin* "${DEPMOD_MOD_DIR}/"

# Generate module dependencies
echo "Generating module dependencies..."
depmod -b $DEPMOD_DIR -e -F $BUILD_DIR/System.map $KERNEL_RELEASE

# Copy generated module dependency files to final location
cp "${DEPMOD_MOD_DIR}"/modules.* $MODULE_DIR/

# # Clean up
# rm -rf $TEMP_MOD_DIR
# rm -rf $DEPMOD_DIR

# Copy kernel image to dist directory
echo "Copying kernel image to dist directory..."
cp $BUILD_DIR/arch/arm64/boot/Image $DIST_DIR/

# Check if build was successful
if [ -f "$DIST_DIR/Image" ] && [ -d "$MODULE_DIR" ]; then
    echo "Kernel build successful!"
    echo "Kernel image: $DIST_DIR/Image"
    echo "Modules directory: $MODULE_DIR"
    echo "Build directory: $BUILD_DIR"
else
    echo "Kernel build failed!"
    exit 1
fi
