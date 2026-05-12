import crypto from 'crypto';

/**
 * 生成模糊指紋哈希
 * 基於 CreepJS 的 getFuzzyHash 邏輯
 */
export async function getFuzzyHash(fp) {
  const metricKeys = [
    'canvas2d.dataURI',
    'canvas2d.emojiSet',
    'canvas2d.emojiURI',
    'canvas2d.liedTextMetrics',
    'canvas2d.mods',
    'canvas2d.paintURI',
    'canvas2d.textMetricsSystemSum',
    'canvas2d.textURI',
    'canvasWebgl.dataURI',
    'canvasWebgl.extensions',
    'canvasWebgl.gpu',
    'canvasWebgl.parameters',
    'canvasWebgl.pixels',
    'canvasWebgl.pixels2',
    'clientRects.domrectSystemSum',
    'clientRects.elementBoundingClientRect',
    'clientRects.elementClientRects',
    'clientRects.emojiSet',
    'consoleErrors.errors',
    'css.computedStyle',
    'css.system',
    'cssMedia.matchMediaCSS',
    'cssMedia.mediaCSS',
    'cssMedia.screenQuery',
    'features.cssFeatures',
    'features.cssVersion',
    'features.jsFeatures',
    'features.jsVersion',
    'features.version',
    'features.windowFeatures',
    'features.windowVersion',
    'fonts.emojiSet',
    'fonts.fontFaceLoadFonts',
    'fonts.platformVersion',
    'fonts.pixelSizeSystemSum',
    'headless.chromium',
    'headless.headless',
    'headless.headlessRating',
    'headless.likeHeadless',
    'headless.likeHeadlessRating',
    'headless.platformEstimate',
    'headless.stealth',
    'headless.stealthRating',
    'headless.systemFonts',
    'intl.dateTimeFormat',
    'intl.displayNames',
    'intl.listFormat',
    'intl.locale',
    'intl.numberFormat',
    'intl.pluralRules',
    'intl.relativeTimeFormat',
    'lies.data',
    'lies.totalLies',
    'maths.data',
    'media.mimeTypes',
    'navigator.appVersion',
    'navigator.bluetoothAvailability',
    'navigator.device',
    'navigator.deviceMemory',
    'navigator.doNotTrack',
    'navigator.globalPrivacyControl',
    'navigator.hardwareConcurrency',
    'navigator.language',
    'navigator.maxTouchPoints',
    'navigator.oscpu',
    'navigator.platform',
    'navigator.system',
    'navigator.userAgent',
    'navigator.userAgentData',
    'navigator.userAgentParsed',
    'navigator.vendor',
    'navigator.webgpu',
    'offlineAudioContext.binsSample',
    'offlineAudioContext.compressorGainReduction',
    'offlineAudioContext.copySample',
    'offlineAudioContext.floatFrequencyDataSum',
    'offlineAudioContext.floatTimeDomainDataSum',
    'offlineAudioContext.noise',
    'offlineAudioContext.sampleSum',
    'offlineAudioContext.totalUniqueSamples',
    'offlineAudioContext.values',
    'resistance.engine',
    'resistance.extension',
    'resistance.mode',
    'resistance.privacy',
    'resistance.security',
    'screen.availHeight',
    'screen.availWidth',
    'screen.colorDepth',
    'screen.height',
    'screen.pixelDepth',
    'screen.touch',
    'screen.width',
    'svg.bBox',
    'svg.computedTextLength',
    'svg.emojiSet',
    'svg.extentOfChar',
    'svg.subStringLength',
    'svg.svgrectSystemSum',
    'timezone.location',
    'timezone.locationEpoch',
    'timezone.locationMeasured',
    'timezone.offset',
    'timezone.offsetComputed',
    'timezone.zone',
    'voices.defaultVoiceLang',
    'voices.defaultVoiceName',
    'voices.languages',
    'voices.local',
    'voices.remote',
    'windowFeatures.apple',
    'windowFeatures.keys',
    'windowFeatures.moz',
    'windowFeatures.webkit',
    'workerScope.device',
    'workerScope.deviceMemory',
    'workerScope.gpu',
    'workerScope.hardwareConcurrency',
    'workerScope.language',
    'workerScope.languages',
    'workerScope.platform',
    'workerScope.system',
    'workerScope.timezoneLocation',
    'workerScope.timezoneOffset',
    'workerScope.userAgent',
    'workerScope.userAgentData',
    'workerScope.webglRenderer',
    'workerScope.webglVendor'
  ];

  // 構建所有指標的映射
  const metricsAll = Object.keys(fp).sort().reduce((acc, sectionKey) => {
    const section = fp[sectionKey];
    if (!section || typeof section !== 'object') return acc;
    
    const sectionMetrics = Object.keys(section || {}).sort().reduce((acc2, key) => {
      if (key === '$hash' || key === 'lied') {
        return acc2;
      }
      return { ...acc2, [`${sectionKey}.${key}`]: section[key] };
    }, {});
    
    return { ...acc, ...sectionMetrics };
  }, {});

  // 減少到 64 個 bin
  const maxBins = 64;
  const binSize = Math.ceil(metricKeys.length / maxBins);

  // 計算模糊指紋主體
  const fuzzyFpMaster = metricKeys.reduce((acc, key, index) => {
    if (!index || (index % binSize === 0)) {
      const keySet = metricKeys.slice(index, index + binSize);
      return {
        ...acc,
        ['' + keySet]: keySet.map((k) => metricsAll[k])
      };
    }
    return acc;
  }, {});

  // 對每個 bin 進行哈希
  const hashedBins = {};
  for (const [key, value] of Object.entries(fuzzyFpMaster)) {
    const json = JSON.stringify(value);
    const hash = crypto.createHash('sha256').update(json).digest('hex');
    hashedBins[key] = hash;
  }

  // 創建模糊哈希（取每個哈希的第一個字符）
  const fuzzyBits = 64;
  const fuzzyFingerprint = Object.keys(hashedBins)
    .map((key) => hashedBins[key][0])
    .join('')
    .padEnd(fuzzyBits, '0');

  return fuzzyFingerprint;
}

