import crypto from 'crypto';

/**
 * 生成 SHA-256 哈希
 */
function hashify(data) {
  const json = JSON.stringify(data);
  const hash = crypto.createHash('sha256').update(json).digest('hex');
  return hash;
}

/**
 * 生成隨機哈希字符串
 */
function randomHash(length = 64) {
  return crypto.randomBytes(length / 2).toString('hex');
}

/**
 * 從數組中隨機選擇
 */
function randomChoice(array) {
  return array[Math.floor(Math.random() * array.length)];
}

/**
 * 生成隨機整數
 */
function randomInt(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

/**
 * 生成隨機浮點數
 */
function randomFloat(min, max, decimals = 2) {
  return parseFloat((Math.random() * (max - min) + min).toFixed(decimals));
}

/**
 * 生成 Worker Scope 數據
 */
export function generateWorkerScope() {
  const platforms = ['Win32', 'Linux x86_64', 'MacIntel', 'Linux armv7l'];
  const systems = ['Windows', 'Linux', 'Mac OS'];
  const languages = ['en-US', 'zh-TW', 'zh-CN', 'ja-JP', 'ko-KR', 'en-GB'];
  const gpuBrands = ['NVIDIA', 'AMD', 'Intel', 'Apple'];
  const gpuModels = [
    'NVIDIA GeForce RTX 4090',
    'AMD Radeon RX 7900 XTX',
    'Intel Iris Xe Graphics',
    'Apple M2 GPU',
    'NVIDIA GeForce RTX 3080',
    'AMD Radeon RX 6800 XT'
  ];

  const platform = randomChoice(platforms);
  const system = randomChoice(systems);
  const language = randomChoice(languages);
  const deviceMemory = randomChoice([2, 4, 8, 16, 32]);
  const hardwareConcurrency = randomChoice([4, 8, 12, 16, 24, 32]);
  const gpuBrand = randomChoice(gpuBrands);
  const gpuModel = randomChoice(gpuModels);

  const data = {
    deviceMemory,
    hardwareConcurrency,
    language,
    languages: [language, language.split('-')[0]],
    platform,
    system,
    device: `${system} Device`,
    timezoneLocation: randomChoice(['Asia/Taipei', 'America/New_York', 'Europe/London', 'Asia/Tokyo']),
    timezoneOffset: randomInt(-12, 12) * 60,
    userAgent: generateUserAgent(system),
    userAgentData: {
      brands: [
        { brand: 'Google Chrome', version: `${randomInt(100, 130)}` },
        { brand: 'Chromium', version: `${randomInt(100, 130)}` }
      ],
      mobile: false,
      platform: system,
      platformVersion: system === 'Windows' ? '10.0.0' : system === 'Mac OS' ? '13.0.0' : '1.0.0',
      architecture: 'x86',
      bitness: '64',
      model: '',
      uaFullVersion: `${randomInt(100, 130)}.0.0.0`
    },
    gpu: {
      compressedGPU: gpuModel,
      confidence: randomChoice(['high', 'medium', 'low']),
      brand: gpuBrand
    },
    webglRenderer: gpuModel,
    webglVendor: gpuBrand,
    localeEntropyIsTrusty: Math.random() > 0.1,
    localeIntlEntropyIsTrusty: Math.random() > 0.1,
    lied: Math.random() < 0.05
  };

  return {
    ...data,
    $hash: hashify(data)
  };
}

/**
 * 生成 User Agent
 */
function generateUserAgent(os) {
  const chromeVersions = Array.from({ length: 30 }, (_, i) => 100 + i);
  const version = randomChoice(chromeVersions);
  
  const uaMap = {
    'Windows': `Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/${version}.0.0.0 Safari/537.36`,
    'Mac OS': `Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/${version}.0.0.0 Safari/537.36`,
    'Linux': `Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/${version}.0.0.0 Safari/537.36`
  };
  
  return uaMap[os] || uaMap['Windows'];
}

/**
 * 生成 Navigator 數據
 */
export function generateNavigator(workerScope) {
  const chromeVersion = randomInt(100, 142);
  const osVersion = workerScope.system === 'Windows' 
    ? '10.0.0' 
    : workerScope.system === 'Mac OS' 
      ? '15.6.1' 
      : '5.0.0';
  
  const data = {
    platform: workerScope.platform,
    system: workerScope.system,
    userAgent: workerScope.userAgent,
    userAgentParsed: `Chrome ${chromeVersion}`,
    device: workerScope.device,
    deviceMemory: workerScope.deviceMemory,
    hardwareConcurrency: workerScope.hardwareConcurrency,
    maxTouchPoints: randomInt(0, 5),
    oscpu: workerScope.system === 'Windows' ? 'Windows NT 10.0; Win64; x64' : undefined,
    vendor: 'Google Inc.',
    appVersion: `5.0 (${workerScope.platform}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/${chromeVersion}.0.0.0 Safari/537.36`,
    userAgentData: {
      ...workerScope.userAgentData,
      platformVersion: osVersion,
      uaFullVersion: `${chromeVersion}.0.${randomInt(7000, 8000)}.${randomInt(100, 200)}`
    },
    bluetoothAvailability: Math.random() > 0.5,
    doNotTrack: randomChoice(['1', '0', null]),
    globalPrivacyControl: Math.random() > 0.7,
    language: workerScope.language,
    languages: workerScope.languages,
    mimeTypes: generateMimeTypes(),
    plugins: generatePlugins(),
    permissions: generatePermissions(),
    webgpu: Math.random() > 0.3,
    lied: Math.random() < 0.05
  };

  return {
    ...data,
    $hash: hashify(data)
  };
}

/**
 * 生成 MimeTypes
 */
function generateMimeTypes() {
  const types = [
    'application/pdf',
    'application/x-google-chrome-pdf',
    'text/html',
    'image/png',
    'image/jpeg'
  ];
  return types.map(type => ({
    type,
    description: type,
    suffixes: type.split('/')[1]
  }));
}

/**
 * 生成 Plugins
 */
function generatePlugins() {
  return [
    {
      name: 'Chrome PDF Plugin',
      description: 'Portable Document Format',
      filename: 'internal-pdf-viewer'
    },
    {
      name: 'Chromium PDF Plugin',
      description: 'Portable Document Format',
      filename: 'internal-pdf-viewer'
    }
  ];
}

/**
 * 生成 Permissions
 */
function generatePermissions() {
  return {
    notifications: randomChoice(['granted', 'denied', 'prompt']),
    geolocation: randomChoice(['granted', 'denied', 'prompt']),
    camera: randomChoice(['granted', 'denied', 'prompt']),
    microphone: randomChoice(['granted', 'denied', 'prompt'])
  };
}

/**
 * 生成 Screen 數據
 */
export function generateScreen() {
  const commonResolutions = [
    { width: 1920, height: 1080 },
    { width: 2560, height: 1440 },
    { width: 3840, height: 2160 },
    { width: 1366, height: 768 },
    { width: 1440, height: 900 },
    { width: 1536, height: 864 }
  ];

  const resolution = randomChoice(commonResolutions);
  const taskbarHeight = randomInt(0, 50);

  const data = {
    width: resolution.width,
    height: resolution.height,
    availWidth: resolution.width,
    availHeight: resolution.height - taskbarHeight,
    colorDepth: randomChoice([24, 30, 32]),
    pixelDepth: randomChoice([24, 30, 32]),
    touch: Math.random() < 0.2,
    lied: Math.random() < 0.05
  };

  return {
    ...data,
    $hash: hashify(data)
  };
}

/**
 * 生成 Canvas 2D 數據
 */
export function generateCanvas2D() {
  const data = {
    dataURI: `data:image/png;base64,${randomHash(100)}`,
    paintURI: `data:image/png;base64,${randomHash(100)}`,
    textURI: `data:image/png;base64,${randomHash(100)}`,
    emojiURI: `data:image/png;base64,${randomHash(100)}`,
    textMetricsSystemSum: randomInt(1000, 10000),
    emojiSet: Array.from({ length: randomInt(10, 50) }, () => 
      String.fromCodePoint(randomInt(0x1F300, 0x1F9FF))
    ),
    mods: randomInt(0, 10),
    lied: Math.random() < 0.1,
    liedTextMetrics: Math.random() < 0.1
  };

  return {
    ...data,
    $hash: hashify(data)
  };
}

/**
 * 生成 WebGL 數據
 */
export function generateCanvasWebGL(workerScope) {
  const extensions = [
    'ANGLE_instanced_arrays',
    'EXT_blend_minmax',
    'EXT_color_buffer_half_float',
    'EXT_disjoint_timer_query',
    'EXT_float_blend',
    'EXT_frag_depth',
    'EXT_shader_texture_lod',
    'EXT_texture_compression_bptc',
    'EXT_texture_compression_rgtc',
    'EXT_texture_filter_anisotropic',
    'WEBKIT_EXT_texture_filter_anisotropic',
    'EXT_sRGB',
    'OES_element_index_uint',
    'OES_fbo_render_mipmap',
    'OES_standard_derivatives',
    'OES_texture_float',
    'OES_texture_float_linear',
    'OES_texture_half_float',
    'OES_texture_half_float_linear',
    'OES_vertex_array_object',
    'WEBGL_color_buffer_float',
    'WEBGL_compressed_texture_s3tc',
    'WEBKIT_WEBGL_compressed_texture_s3tc',
    'WEBGL_compressed_texture_s3tc_srgb',
    'WEBGL_debug_renderer_info',
    'WEBGL_debug_shaders',
    'WEBGL_depth_texture',
    'WEBKIT_WEBGL_depth_texture',
    'WEBGL_draw_buffers',
    'WEBGL_lose_context',
    'WEBKIT_WEBGL_lose_context'
  ];

  const parameters = {
    MAX_TEXTURE_SIZE: randomChoice([16384, 8192, 4096]),
    MAX_CUBE_MAP_TEXTURE_SIZE: randomChoice([16384, 8192, 4096]),
    MAX_RENDERBUFFER_SIZE: randomChoice([16384, 8192, 4096]),
    MAX_VIEWPORT_DIMS: [randomInt(8000, 16000), randomInt(8000, 16000)],
    MAX_VERTEX_ATTRIBS: randomChoice([16, 32]),
    MAX_VERTEX_UNIFORM_VECTORS: randomChoice([1024, 2048, 4096]),
    MAX_VERTEX_TEXTURE_IMAGE_UNITS: randomChoice([16, 32]),
    MAX_FRAGMENT_UNIFORM_VECTORS: randomChoice([1024, 2048, 4096]),
    MAX_TEXTURE_IMAGE_UNITS: randomChoice([16, 32]),
    ALIASED_POINT_SIZE_RANGE: [1, randomInt(100, 1000)],
    ALIASED_LINE_WIDTH_RANGE: [1, randomInt(1, 10)],
    UNMASKED_RENDERER_WEBGL: workerScope.gpu.compressedGPU,
    UNMASKED_VENDOR_WEBGL: workerScope.gpu.brand
  };

  const data = {
    dataURI: `data:image/png;base64,${randomHash(100)}`,
    dataURI2: `data:image/png;base64,${randomHash(100)}`,
    extensions: extensions.slice(0, randomInt(15, extensions.length)),
    parameters,
    gpu: workerScope.gpu,
    pixels: Array.from({ length: randomInt(100, 1000) }, () => randomInt(0, 255)),
    pixels2: Array.from({ length: randomInt(100, 1000) }, () => randomInt(0, 255)),
    lied: Math.random() < 0.1,
    parameterOrExtensionLie: Math.random() < 0.05
  };

  return {
    ...data,
    pixels: hashify(data.pixels),
    pixels2: hashify(data.pixels2),
    $hash: hashify(data)
  };
}

/**
 * 生成 Timezone 數據
 */
export function generateTimezone() {
  const timezones = [
    'Asia/Taipei',
    'America/New_York',
    'Europe/London',
    'Asia/Tokyo',
    'America/Los_Angeles',
    'Europe/Paris',
    'Asia/Shanghai',
    'Australia/Sydney'
  ];

  const zone = randomChoice(timezones);
  const offset = randomInt(-12, 12) * 60;

  const data = {
    zone,
    offset,
    offsetComputed: offset,
    location: zone,
    locationMeasured: zone,
    locationEpoch: Date.now(),
    lied: Math.random() < 0.05
  };

  return {
    ...data,
    $hash: hashify(data)
  };
}

/**
 * 生成 Intl 數據
 */
export function generateIntl() {
  const locales = ['zh-TW', 'en-US', 'ja-JP', 'ko-KR'];
  const locale = randomChoice(locales);
  
  const dateTimeFormats = {
    'zh-TW': '7月 台北標準時間',
    'en-US': 'July Pacific Standard Time',
    'ja-JP': '7月 日本標準時',
    'ko-KR': '7월 한국 표준시'
  };
  
  const displayNames = {
    'zh-TW': '英文(美國)',
    'en-US': 'English (United States)',
    'ja-JP': '英語（米国）',
    'ko-KR': '영어(미국)'
  };
  
  const numberFormats = {
    'zh-TW': '2100萬',
    'en-US': '21M',
    'ja-JP': '2100万',
    'ko-KR': '2100만'
  };
  
  const relativeTimeFormats = {
    'zh-TW': '明年',
    'en-US': 'next year',
    'ja-JP': '来年',
    'ko-KR': '내년'
  };
  
  const pluralRules = {
    'zh-TW': 'other',
    'en-US': 'one',
    'ja-JP': 'other',
    'ko-KR': 'other'
  };
  
  const listFormats = {
    'zh-TW': '0或1',
    'en-US': '0 or 1',
    'ja-JP': '0または1',
    'ko-KR': '0 또는 1'
  };

  const data = {
    locale,
    dateTimeFormat: dateTimeFormats[locale] || dateTimeFormats['en-US'],
    displayNames: displayNames[locale] || displayNames['en-US'],
    numberFormat: numberFormats[locale] || numberFormats['en-US'],
    relativeTimeFormat: relativeTimeFormats[locale] || relativeTimeFormats['en-US'],
    pluralRules: pluralRules[locale] || pluralRules['en-US'],
    listFormat: listFormats[locale] || listFormats['en-US'],
    lied: Math.random() < 0.05
  };

  return {
    ...data,
    $hash: hashify(data)
  };
}

/**
 * 生成 Fonts 數據
 */
export function generateFonts() {
  const commonFonts = [
    'Arial', 'Helvetica', 'Times New Roman', 'Courier New', 'Verdana',
    'Georgia', 'Palatino', 'Garamond', 'Bookman', 'Comic Sans MS',
    'Trebuchet MS', 'Arial Black', 'Impact', 'Tahoma', 'Lucida Console',
    'Microsoft YaHei', 'SimSun', 'SimHei', 'KaiTi', 'FangSong'
  ];

  const platformVersions = {
    'Windows': 'Windows 10',
    'Mac OS': 'macOS 13.0',
    'Linux': 'Linux 5.0'
  };

  const data = {
    fontFaceLoadFonts: commonFonts.slice(0, randomInt(5, commonFonts.length)),
    platformVersion: platformVersions[randomChoice(Object.keys(platformVersions))],
    emojiSet: Array.from({ length: randomInt(10, 30) }, () => 
      String.fromCodePoint(randomInt(0x1F300, 0x1F9FF))
    ),
    pixelSizeSystemSum: randomInt(1000, 10000),
    apps: [],
    lied: Math.random() < 0.1
  };

  return {
    ...data,
    $hash: hashify(data)
  };
}

/**
 * 生成 Audio 數據
 */
export function generateOfflineAudioContext() {
  const data = {
    sampleSum: randomInt(1000, 10000),
    totalUniqueSamples: randomInt(100, 1000),
    floatFrequencyDataSum: randomFloat(-1000, 1000),
    floatTimeDomainDataSum: randomFloat(-1000, 1000),
    compressorGainReduction: randomFloat(-60, 0),
    binsSample: randomInt(100, 1000),
    copySample: randomInt(100, 1000),
    noise: randomFloat(0, 1),
    values: Array.from({ length: randomInt(10, 100) }, () => randomFloat(-1, 1)),
    lied: Math.random() < 0.1
  };

  return {
    ...data,
    $hash: hashify(data)
  };
}

/**
 * 生成 Voices 數據
 */
export function generateVoices() {
  const voices = [
    { name: 'Google US English', lang: 'en-US', local: true },
    { name: 'Microsoft Zira', lang: 'en-US', local: true },
    { name: 'Microsoft David', lang: 'en-US', local: true },
    { name: 'Google 中文（台灣）', lang: 'zh-TW', local: true },
    { name: 'Microsoft Yaoyao', lang: 'zh-CN', local: true }
  ];

  const selectedVoices = voices.slice(0, randomInt(2, voices.length));

  const data = {
    local: selectedVoices.filter(v => v.local),
    remote: selectedVoices.filter(v => !v.local),
    languages: [...new Set(selectedVoices.map(v => v.lang))],
    defaultVoiceName: selectedVoices[0]?.name,
    defaultVoiceLang: selectedVoices[0]?.lang
  };

  return {
    ...data,
    $hash: hashify(data)
  };
}

/**
 * 生成 Media 數據
 */
export function generateMedia() {
  const mimeTypes = [
    { type: 'audio/mpeg', description: 'MP3 audio' },
    { type: 'video/mp4', description: 'MP4 video' },
    { type: 'audio/ogg', description: 'OGG audio' },
    { type: 'video/webm', description: 'WebM video' },
    { type: 'audio/wav', description: 'WAV audio' },
    { type: 'video/ogg', description: 'OGG video' },
    { type: 'audio/aac', description: 'AAC audio' },
    { type: 'video/quicktime', description: 'QuickTime video' },
    { type: 'audio/flac', description: 'FLAC audio' },
    { type: 'video/x-msvideo', description: 'AVI video' },
    { type: 'audio/webm', description: 'WebM audio' },
    { type: 'video/x-matroska', description: 'MKV video' }
  ];

  const selectedMimeTypes = mimeTypes.slice(0, randomInt(8, mimeTypes.length));

  const data = {
    mimeTypes: selectedMimeTypes,
    devices: []
  };

  return {
    ...data,
    $hash: hashify(data)
  };
}

/**
 * 生成 WebRTC 數據
 */
export function generateWebRTC() {
  const codecs = {
    audio: [
      {
        mimeType: 'audio/opus',
        clockRates: [48000],
        channels: 2,
        sdpFmtpLine: ['minptime=10', 'useinbandfec=1']
      },
      {
        mimeType: 'audio/PCMU',
        clockRates: [8000],
        channels: 1
      },
      {
        mimeType: 'audio/PCMA',
        clockRates: [8000],
        channels: 1
      }
    ],
    video: [
      {
        mimeType: 'video/VP8',
        clockRates: [90000],
        feedbackSupport: ['ccm fir', 'nack', 'nack pli']
      },
      {
        mimeType: 'video/VP9',
        clockRates: [90000],
        feedbackSupport: ['ccm fir', 'nack', 'nack pli']
      },
      {
        mimeType: 'video/H264',
        clockRates: [90000],
        sdpFmtpLine: ['level-asymmetry-allowed=1', 'packetization-mode=1', 'profile-level-id=42001f']
      }
    ]
  };

  const extensions = [
    'urn:ietf:params:rtp-hdrext:sdes:mid',
    'urn:ietf:params:rtp-hdrext:sdes:rtp-stream-id',
    'urn:ietf:params:rtp-hdrext:sdes:repaired-rtp-stream-id',
    'urn:3gpp:video-orientation',
    'http://www.webrtc.org/experiments/rtp-hdrext/abs-send-time',
    'http://www.ietf.org/id/draft-holmer-rmcat-transport-wide-cc-extensions-01'
  ];

  // 生成隨機 IP 地址
  const ipAddress = `${randomInt(1, 255)}.${randomInt(1, 255)}.${randomInt(1, 255)}.${randomInt(1, 255)}`;
  const foundation = randomInt(1000000000, 9999999999).toString();
  
  // 生成 ICE candidate
  const port = randomInt(50000, 65000);
  const iceCandidate = `candidate:${foundation} 1 udp 1677729535 ${ipAddress} ${port} typ srflx raddr 0.0.0.0 rport 0 generation 0 ufrag ${randomHash(4).toUpperCase()} network-cost 999`;

  const devices = [];
  if (Math.random() > 0.3) devices.push('mic');
  if (Math.random() > 0.3) devices.push('audio');
  if (Math.random() > 0.3) devices.push('webcam');

  const data = {
    codecsSdp: codecs,
    extensions: extensions.slice(0, randomInt(4, extensions.length)),
    foundation,
    foundationProp: foundation,
    iceCandidate,
    address: ipAddress,
    stunConnection: iceCandidate,
    devices
  };

  return {
    ...data,
    $hash: hashify(data)
  };
}

/**
 * 生成 Status 數據
 */
export function generateStatus() {
  const networkTypes = ['4g', '3g', '2g', 'slow-2g'];
  const effectiveType = randomChoice(networkTypes);
  
  const data = {
    // Battery
    charging: Math.random() > 0.3,
    chargingTime: Math.random() > 0.5 ? Infinity : randomInt(0, 7200) * 1000,
    dischargingTime: Math.random() > 0.5 ? Infinity : randomInt(0, 14400) * 1000,
    level: randomFloat(0.2, 1.0, 2),
    
    // Network
    rtt: randomInt(20, 200),
    downlink: randomFloat(1, 50, 1),
    effectiveType,
    saveData: Math.random() < 0.1,
    downlinkMax: randomFloat(10, 100, 1),
    type: effectiveType,
    
    // Storage
    quota: randomInt(100000000000, 500000000000), // bytes
    quotaInGigabytes: null, // will be calculated
    quotaIsInsecure: Math.random() < 0.05,
    
    // Memory
    memory: randomInt(2000000000, 8000000000), // bytes
    memoryInGigabytes: null, // will be calculated
    
    // Timing
    timingRes: [randomFloat(0.01, 0.1, 10), randomFloat(0.01, 0.1, 10)],
    stackSize: randomInt(10000, 20000),
    
    // Scripts
    scripts: [],
    scriptSize: randomInt(100000, 500000),
    clientLitter: []
  };
  
  // 計算 GB
  data.quotaInGigabytes = parseFloat((data.quota / 1073741824).toFixed(2));
  data.memoryInGigabytes = parseFloat((data.memory / 1073741824).toFixed(2));

  return {
    ...data,
    $hash: hashify(data)
  };
}

/**
 * 生成 CSS Media 數據
 */
export function generateCSSMedia(screen) {
  const data = {
    mediaCSS: {
      'prefers-reduced-motion': randomChoice(['no-preference', 'reduce']),
      'prefers-color-scheme': randomChoice(['light', 'dark']),
      'monochrome': randomInt(0, 8),
      'inverted-colors': randomChoice(['none', 'inverted']),
      'forced-colors': randomChoice(['none', 'active']),
      'any-hover': randomChoice(['none', 'hover']),
      'hover': randomChoice(['none', 'hover']),
      'any-pointer': randomChoice(['none', 'coarse', 'fine']),
      'pointer': randomChoice(['none', 'coarse', 'fine']),
      'color-gamut': randomChoice(['srgb', 'p3', 'rec2020'])
    },
    screenQuery: {
      width: screen.width,
      height: screen.height
    }
  };

  return {
    ...data,
    $hash: hashify(data)
  };
}

/**
 * 生成 CSS 數據
 */
export function generateCSS() {
  const systemFonts = [
    'Arial', 'Helvetica', 'Times New Roman', 'Courier New', 'Verdana',
    'Georgia', 'Palatino', 'Garamond', 'Microsoft YaHei', 'SimSun'
  ];

  const data = {
    system: {
      fonts: systemFonts.slice(0, randomInt(5, systemFonts.length))
    },
    computedStyle: {}
  };

  return {
    ...data,
    $hash: hashify(data)
  };
}

/**
 * 生成 Lies 數據
 */
export function generateLies() {
  const lieTypes = [
    'failed toString',
    'failed descriptor',
    'failed own property',
    'failed at incompatible proxy error'
  ];

  const data = {
    data: {},
    totalLies: 0
  };

  if (Math.random() < 0.3) {
    const numLies = randomInt(1, 5);
    data.totalLies = numLies;
    for (let i = 0; i < numLies; i++) {
      const api = randomChoice(['Navigator.userAgent', 'Screen.width', 'Canvas.getImageData']);
      data.data[api] = [randomChoice(lieTypes)];
    }
  }

  return {
    ...data,
    $hash: hashify(data)
  };
}

/**
 * 生成 Resistance 數據
 */
export function generateResistance() {
  const privacyModes = ['none', 'tor browser', 'firefox', 'brave', 'unknown'];
  const securityModes = ['none', 'strict', 'standard', 'unknown'];
  const extensions = ['none', 'uBlock Origin', 'Privacy Badger', 'NoScript', 'CanvasBlocker', 'unknown'];

  const data = {
    privacy: randomChoice(privacyModes),
    security: randomChoice(securityModes),
    mode: randomChoice(['allow', 'standard', 'strict', 'unknown']),
    extension: randomChoice(extensions),
    engine: randomChoice(['Blink', 'Gecko', 'WebKit'])
  };

  return {
    ...data,
    $hash: hashify(data)
  };
}

/**
 * 生成 Headless 數據
 */
export function generateHeadless() {
  const likeHeadlessRating = randomInt(0, 50);
  const headlessRating = randomInt(0, 10);
  const stealthRating = randomInt(0, 10);
  
  const data = {
    chromium: Math.random() > 0.3,
    likeHeadless: {
      noChrome: Math.random() < 0.1,
      hasPermissionsBug: Math.random() < 0.1,
      noPlugins: Math.random() < 0.1,
      noMimeTypes: Math.random() < 0.1,
      notificationIsDenied: Math.random() < 0.2,
      hasKnownBgColor: Math.random() < 0.1,
      prefersLightColor: Math.random() > 0.5,
      uaDataIsBlank: Math.random() < 0.1,
      pdfIsDisabled: Math.random() < 0.1,
      noTaskbar: Math.random() < 0.1
    },
    headless: {
      automationControlled: Math.random() < 0.05,
      webdriver: Math.random() < 0.05,
      chromeRuntime: Math.random() < 0.05
    },
    stealth: {},
    headlessRating,
    likeHeadlessRating,
    stealthRating,
    platformEstimate: [randomChoice(['Windows', 'Mac OS', 'Linux'])],
    systemFonts: [randomChoice(['Arial', 'Helvetica', 'Times New Roman'])]
  };

  return {
    ...data,
    $hash: hashify(data)
  };
}

/**
 * 生成完整的 Fingerprint 對象
 */
export function generateFingerprint() {
  const workerScope = generateWorkerScope();
  const navigator = generateNavigator(workerScope);
  const screen = generateScreen();
  const canvas2d = generateCanvas2D();
  const canvasWebgl = generateCanvasWebGL(workerScope);
  const timezone = generateTimezone();
  const fonts = generateFonts();
  const offlineAudioContext = generateOfflineAudioContext();
  const voices = generateVoices();
  const media = generateMedia();
  const cssMedia = generateCSSMedia(screen);
  const css = generateCSS();
  const lies = generateLies();
  const resistance = generateResistance();
  const headless = generateHeadless();
  const webrtc = generateWebRTC();
  const status = generateStatus();
  const intl = generateIntl();

  const fingerprint = {
    workerScope,
    navigator,
    windowFeatures: {
      keys: [],
      apple: {},
      moz: {},
      webkit: {},
      $hash: randomHash(64)
    },
    headless,
    htmlElementVersion: {
      keys: [],
      $hash: randomHash(64)
    },
    cssMedia,
    css,
    screen,
    voices,
    media,
    canvas2d,
    canvasWebgl,
    maths: {
      data: Array.from({ length: randomInt(10, 50) }, () => randomFloat(-100, 100)),
      $hash: randomHash(64)
    },
    consoleErrors: {
      errors: [],
      $hash: randomHash(64)
    },
    timezone,
    clientRects: {
      elementBoundingClientRect: [],
      elementClientRects: [],
      rangeBoundingClientRect: [],
      rangeClientRects: [],
      emojiSet: [],
      domrectSystemSum: randomInt(1000, 10000),
      $hash: randomHash(64)
    },
    offlineAudioContext,
    fonts,
    lies,
    trash: {
      trashBin: [],
      $hash: randomHash(64)
    },
    capturedErrors: {
      data: [],
      $hash: randomHash(64)
    },
    svg: {
      bBox: [],
      computedTextLength: [],
      emojiSet: [],
      extentOfChar: [],
      subStringLength: [],
      svgrectSystemSum: randomInt(1000, 10000),
      $hash: randomHash(64)
    },
    resistance,
    intl,
    features: {
      version: randomInt(100, 130),
      versionRange: [randomInt(100, 130)],
      jsVersion: randomInt(100, 130),
      cssVersion: randomInt(100, 130),
      windowVersion: randomInt(100, 130),
      jsFeatures: {},
      cssFeatures: {},
      windowFeatures: {},
      jsFeaturesKeys: [],
      $hash: randomHash(64)
    },
    webrtc,
    status
  };

  return fingerprint;
}

/**
 * 生成 Creep (Stable Fingerprint) 對象
 */
export function generateCreep(fingerprint) {
  const creep = {
    navigator: fingerprint.navigator?.lied ? undefined : {
      bluetoothAvailability: fingerprint.navigator?.bluetoothAvailability,
      device: fingerprint.navigator?.device,
      deviceMemory: fingerprint.navigator?.deviceMemory,
      hardwareConcurrency: fingerprint.navigator?.hardwareConcurrency,
      maxTouchPoints: fingerprint.navigator?.maxTouchPoints,
      oscpu: fingerprint.navigator?.oscpu,
      platform: fingerprint.navigator?.platform,
      system: fingerprint.navigator?.system,
      userAgentData: fingerprint.navigator?.userAgentData,
      vendor: fingerprint.navigator?.vendor
    },
    screen: fingerprint.screen?.lied ? undefined : {
      height: fingerprint.screen?.height,
      width: fingerprint.screen?.width,
      pixelDepth: fingerprint.screen?.pixelDepth,
      colorDepth: fingerprint.screen?.colorDepth,
      lied: fingerprint.screen?.lied
    },
    workerScope: fingerprint.workerScope?.lied ? undefined : {
      deviceMemory: fingerprint.workerScope?.deviceMemory,
      hardwareConcurrency: fingerprint.workerScope?.hardwareConcurrency,
      language: fingerprint.workerScope?.language,
      platform: fingerprint.workerScope?.platform,
      system: fingerprint.workerScope?.system,
      device: fingerprint.workerScope?.device,
      timezoneLocation: fingerprint.workerScope?.timezoneLocation,
      webglRenderer: fingerprint.workerScope?.webglRenderer,
      webglVendor: fingerprint.workerScope?.webglVendor,
      userAgentData: fingerprint.workerScope?.userAgentData
    },
    media: fingerprint.media,
    canvas2d: fingerprint.canvas2d?.lied ? undefined : {
      lied: fingerprint.canvas2d?.lied,
      dataURI: fingerprint.canvas2d?.dataURI,
      paintURI: fingerprint.canvas2d?.paintURI,
      textURI: fingerprint.canvas2d?.textURI,
      emojiURI: fingerprint.canvas2d?.emojiURI,
      textMetricsSystemSum: fingerprint.canvas2d?.textMetricsSystemSum,
      emojiSet: fingerprint.canvas2d?.emojiSet
    },
    canvasWebgl: fingerprint.canvasWebgl?.lied ? undefined : {
      extensions: fingerprint.canvasWebgl?.extensions,
      gpu: fingerprint.canvasWebgl?.gpu,
      lied: fingerprint.canvasWebgl?.lied,
      parameterOrExtensionLie: fingerprint.canvasWebgl?.parameterOrExtensionLie,
      parameters: fingerprint.canvasWebgl?.parameters
    },
    cssMedia: fingerprint.cssMedia ? {
      reducedMotion: fingerprint.cssMedia?.mediaCSS?.['prefers-reduced-motion'],
      colorScheme: fingerprint.cssMedia?.mediaCSS?.['prefers-color-scheme'],
      monochrome: fingerprint.cssMedia?.mediaCSS?.monochrome,
      invertedColors: fingerprint.cssMedia?.mediaCSS?.['inverted-colors'],
      forcedColors: fingerprint.cssMedia?.mediaCSS?.['forced-colors'],
      anyHover: fingerprint.cssMedia?.mediaCSS?.['any-hover'],
      hover: fingerprint.cssMedia?.mediaCSS?.hover,
      anyPointer: fingerprint.cssMedia?.mediaCSS?.['any-pointer'],
      pointer: fingerprint.cssMedia?.mediaCSS?.pointer,
      colorGamut: fingerprint.cssMedia?.mediaCSS?.['color-gamut'],
      screenQuery: fingerprint.cssMedia?.screenQuery
    } : undefined,
    css: fingerprint.css ? fingerprint.css.system.fonts : undefined,
    timezone: fingerprint.timezone?.lied ? undefined : {
      locationMeasured: fingerprint.timezone?.locationMeasured,
      lied: fingerprint.timezone?.lied
    },
    offlineAudioContext: fingerprint.offlineAudioContext?.lied ? undefined : fingerprint.offlineAudioContext,
    fonts: fingerprint.fonts?.lied ? undefined : fingerprint.fonts?.fontFaceLoadFonts,
    forceRenew: Date.now()
  };

  return creep;
}

