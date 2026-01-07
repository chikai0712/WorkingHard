import Database from 'better-sqlite3';
import path from 'path';
import { fileURLToPath } from 'url';
import crypto from 'crypto';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

/**
 * 簡單的哈希函數（用於生成指紋哈希）
 */
function hashify(data) {
  const json = JSON.stringify(data);
  return crypto.createHash('sha256').update(json).digest('hex');
}

/**
 * 數據庫連接類
 */
export class CreepDatabase {
  constructor(dbPath = null) {
    this.dbPath = dbPath || path.join(__dirname, '../data/creepjs_fingerprints.db');
    this.db = null;
  }

  /**
   * 連接數據庫
   */
  connect() {
    try {
      this.db = new Database(this.dbPath);
      this.db.pragma('journal_mode = WAL');
      console.log(`✓ 數據庫連接成功: ${this.dbPath}`);
      return true;
    } catch (error) {
      console.error('✗ 數據庫連接失敗:', error.message);
      return false;
    }
  }

  /**
   * 初始化數據表
   */
  initialize() {
    if (!this.db) {
      throw new Error('數據庫未連接');
    }

    // 創建指紋主表
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS fingerprints (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        timestamp INTEGER NOT NULL,
        fingerprint_hash TEXT UNIQUE,
        creep_hash TEXT,
        fuzzy_hash TEXT,
        time_end REAL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
      );

      CREATE INDEX IF NOT EXISTS idx_fingerprint_hash ON fingerprints(fingerprint_hash);
      CREATE INDEX IF NOT EXISTS idx_creep_hash ON fingerprints(creep_hash);
      CREATE INDEX IF NOT EXISTS idx_timestamp ON fingerprints(timestamp);
      CREATE INDEX IF NOT EXISTS idx_session_id ON fingerprints(session_id);
    `);

    // 創建詳細數據表（JSON 存儲）
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS fingerprint_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fingerprint_id INTEGER NOT NULL,
        data_type TEXT NOT NULL,
        data_json TEXT NOT NULL,
        FOREIGN KEY (fingerprint_id) REFERENCES fingerprints(id) ON DELETE CASCADE
      );

      CREATE INDEX IF NOT EXISTS idx_fingerprint_id ON fingerprint_data(fingerprint_id);
      CREATE INDEX IF NOT EXISTS idx_data_type ON fingerprint_data(data_type);
    `);

    // 創建 Worker Scope 表
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS worker_scope (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fingerprint_id INTEGER NOT NULL,
        device_memory INTEGER,
        hardware_concurrency INTEGER,
        language TEXT,
        platform TEXT,
        system TEXT,
        device TEXT,
        timezone_location TEXT,
        timezone_offset INTEGER,
        user_agent TEXT,
        gpu_compressed TEXT,
        gpu_brand TEXT,
        gpu_confidence TEXT,
        webgl_renderer TEXT,
        webgl_vendor TEXT,
        hash TEXT,
        lied BOOLEAN,
        FOREIGN KEY (fingerprint_id) REFERENCES fingerprints(id) ON DELETE CASCADE
      );

      CREATE INDEX IF NOT EXISTS idx_ws_fingerprint_id ON worker_scope(fingerprint_id);
      CREATE INDEX IF NOT EXISTS idx_ws_gpu ON worker_scope(gpu_compressed);
    `);

    // 創建 Navigator 表
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS navigator (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fingerprint_id INTEGER NOT NULL,
        platform TEXT,
        system TEXT,
        user_agent TEXT,
        user_agent_parsed TEXT,
        device TEXT,
        device_memory INTEGER,
        hardware_concurrency INTEGER,
        max_touch_points INTEGER,
        oscpu TEXT,
        vendor TEXT,
        app_version TEXT,
        bluetooth_availability BOOLEAN,
        do_not_track TEXT,
        global_privacy_control BOOLEAN,
        language TEXT,
        hash TEXT,
        lied BOOLEAN,
        FOREIGN KEY (fingerprint_id) REFERENCES fingerprints(id) ON DELETE CASCADE
      );

      CREATE INDEX IF NOT EXISTS idx_nav_fingerprint_id ON navigator(fingerprint_id);
      CREATE INDEX IF NOT EXISTS idx_nav_user_agent ON navigator(user_agent);
    `);

    // 創建 Screen 表
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS screen (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fingerprint_id INTEGER NOT NULL,
        width INTEGER,
        height INTEGER,
        avail_width INTEGER,
        avail_height INTEGER,
        color_depth INTEGER,
        pixel_depth INTEGER,
        touch BOOLEAN,
        hash TEXT,
        lied BOOLEAN,
        FOREIGN KEY (fingerprint_id) REFERENCES fingerprints(id) ON DELETE CASCADE
      );

      CREATE INDEX IF NOT EXISTS idx_screen_fingerprint_id ON screen(fingerprint_id);
    `);

    // 創建 Canvas 表
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS canvas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fingerprint_id INTEGER NOT NULL,
        canvas_type TEXT NOT NULL,
        data_uri TEXT,
        paint_uri TEXT,
        text_uri TEXT,
        emoji_uri TEXT,
        text_metrics_system_sum INTEGER,
        emoji_set TEXT,
        mods INTEGER,
        hash TEXT,
        lied BOOLEAN,
        lied_text_metrics BOOLEAN,
        FOREIGN KEY (fingerprint_id) REFERENCES fingerprints(id) ON DELETE CASCADE
      );

      CREATE INDEX IF NOT EXISTS idx_canvas_fingerprint_id ON canvas(fingerprint_id);
      CREATE INDEX IF NOT EXISTS idx_canvas_type ON canvas(canvas_type);
    `);

    // 創建 WebGL 表
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS webgl (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fingerprint_id INTEGER NOT NULL,
        data_uri TEXT,
        data_uri2 TEXT,
        extensions TEXT,
        parameters_json TEXT,
        gpu_compressed TEXT,
        gpu_brand TEXT,
        gpu_confidence TEXT,
        pixels_hash TEXT,
        pixels2_hash TEXT,
        hash TEXT,
        lied BOOLEAN,
        parameter_or_extension_lie BOOLEAN,
        FOREIGN KEY (fingerprint_id) REFERENCES fingerprints(id) ON DELETE CASCADE
      );

      CREATE INDEX IF NOT EXISTS idx_webgl_fingerprint_id ON webgl(fingerprint_id);
      CREATE INDEX IF NOT EXISTS idx_webgl_gpu ON webgl(gpu_compressed);
    `);

    // 創建 Timezone 表
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS timezone (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fingerprint_id INTEGER NOT NULL,
        zone TEXT,
        offset INTEGER,
        offset_computed INTEGER,
        location TEXT,
        location_measured TEXT,
        location_epoch INTEGER,
        hash TEXT,
        lied BOOLEAN,
        FOREIGN KEY (fingerprint_id) REFERENCES fingerprints(id) ON DELETE CASCADE
      );

      CREATE INDEX IF NOT EXISTS idx_tz_fingerprint_id ON timezone(fingerprint_id);
      CREATE INDEX IF NOT EXISTS idx_tz_zone ON timezone(zone);
    `);

    // 創建 Fonts 表
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS fonts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fingerprint_id INTEGER NOT NULL,
        font_face_load_fonts TEXT,
        platform_version TEXT,
        emoji_set TEXT,
        pixel_size_system_sum INTEGER,
        hash TEXT,
        lied BOOLEAN,
        FOREIGN KEY (fingerprint_id) REFERENCES fingerprints(id) ON DELETE CASCADE
      );

      CREATE INDEX IF NOT EXISTS idx_fonts_fingerprint_id ON fonts(fingerprint_id);
    `);

    // 創建 Audio 表
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS audio (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fingerprint_id INTEGER NOT NULL,
        sample_sum INTEGER,
        total_unique_samples INTEGER,
        float_frequency_data_sum REAL,
        float_time_domain_data_sum REAL,
        compressor_gain_reduction REAL,
        bins_sample INTEGER,
        copy_sample INTEGER,
        noise REAL,
        hash TEXT,
        lied BOOLEAN,
        FOREIGN KEY (fingerprint_id) REFERENCES fingerprints(id) ON DELETE CASCADE
      );

      CREATE INDEX IF NOT EXISTS idx_audio_fingerprint_id ON audio(fingerprint_id);
    `);

    // 創建 Resistance 表
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS resistance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fingerprint_id INTEGER NOT NULL,
        privacy TEXT,
        security TEXT,
        mode TEXT,
        extension TEXT,
        engine TEXT,
        hash TEXT,
        FOREIGN KEY (fingerprint_id) REFERENCES fingerprints(id) ON DELETE CASCADE
      );

      CREATE INDEX IF NOT EXISTS idx_resistance_fingerprint_id ON resistance(fingerprint_id);
      CREATE INDEX IF NOT EXISTS idx_resistance_privacy ON resistance(privacy);
    `);

    // 創建 Headless 表
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS headless (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fingerprint_id INTEGER NOT NULL,
        chromium BOOLEAN,
        headless_rating INTEGER,
        like_headless_rating INTEGER,
        stealth_rating INTEGER,
        platform_estimate TEXT,
        hash TEXT,
        FOREIGN KEY (fingerprint_id) REFERENCES fingerprints(id) ON DELETE CASCADE
      );

      CREATE INDEX IF NOT EXISTS idx_headless_fingerprint_id ON headless(fingerprint_id);
    `);

    // 創建 Lies 表
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS lies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fingerprint_id INTEGER NOT NULL,
        total_lies INTEGER,
        lies_json TEXT,
        hash TEXT,
        FOREIGN KEY (fingerprint_id) REFERENCES fingerprints(id) ON DELETE CASCADE
      );

      CREATE INDEX IF NOT EXISTS idx_lies_fingerprint_id ON lies(fingerprint_id);
    `);

    console.log('✓ 數據表初始化完成');
  }

  /**
   * 插入指紋數據
   */
  insertFingerprint(sessionId, fingerprint, creep, fuzzyHash, timeEnd) {
    if (!this.db) {
      throw new Error('數據庫未連接');
    }

    const transaction = this.db.transaction(() => {
      const fpHash = fingerprint.workerScope?.$hash || 
                    hashify(fingerprint);
      const cHash = hashify(creep);

      // 插入主記錄
      const insertFp = this.db.prepare(`
        INSERT INTO fingerprints (
          session_id, timestamp, fingerprint_hash, creep_hash, fuzzy_hash, time_end
        ) VALUES (?, ?, ?, ?, ?, ?)
      `);

      const result = insertFp.run(
        sessionId,
        Date.now(),
        fpHash,
        cHash,
        fuzzyHash || null,
        timeEnd || null
      );

      const fingerprintId = result.lastInsertRowid;

      // 插入 Worker Scope
      if (fingerprint.workerScope) {
        const ws = fingerprint.workerScope;
        this.db.prepare(`
          INSERT INTO worker_scope (
            fingerprint_id, device_memory, hardware_concurrency, language,
            platform, system, device, timezone_location, timezone_offset,
            user_agent, gpu_compressed, gpu_brand, gpu_confidence,
            webgl_renderer, webgl_vendor, hash, lied
          ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        `).run(
          fingerprintId,
          ws.deviceMemory || null,
          ws.hardwareConcurrency || null,
          ws.language || null,
          ws.platform || null,
          ws.system || null,
          ws.device || null,
          ws.timezoneLocation || null,
          ws.timezoneOffset || null,
          ws.userAgent || null,
          ws.gpu?.compressedGPU || null,
          ws.gpu?.brand || null,
          ws.gpu?.confidence || null,
          ws.webglRenderer || null,
          ws.webglVendor || null,
          ws.$hash || null,
          ws.lied || false
        );
      }

      // 插入 Navigator
      if (fingerprint.navigator) {
        const nav = fingerprint.navigator;
        this.db.prepare(`
          INSERT INTO navigator (
            fingerprint_id, platform, system, user_agent, user_agent_parsed,
            device, device_memory, hardware_concurrency, max_touch_points,
            oscpu, vendor, app_version, bluetooth_availability,
            do_not_track, global_privacy_control, language, hash, lied
          ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        `).run(
          fingerprintId,
          nav.platform || null,
          nav.system || null,
          nav.userAgent || null,
          nav.userAgentParsed || null,
          nav.device || null,
          nav.deviceMemory || null,
          nav.hardwareConcurrency || null,
          nav.maxTouchPoints || null,
          nav.oscpu || null,
          nav.vendor || null,
          nav.appVersion || null,
          nav.bluetoothAvailability || null,
          nav.doNotTrack || null,
          nav.globalPrivacyControl || null,
          nav.language || null,
          nav.$hash || null,
          nav.lied || false
        );
      }

      // 插入 Screen
      if (fingerprint.screen) {
        const screen = fingerprint.screen;
        this.db.prepare(`
          INSERT INTO screen (
            fingerprint_id, width, height, avail_width, avail_height,
            color_depth, pixel_depth, touch, hash, lied
          ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        `).run(
          fingerprintId,
          screen.width || null,
          screen.height || null,
          screen.availWidth || null,
          screen.availHeight || null,
          screen.colorDepth || null,
          screen.pixelDepth || null,
          screen.touch || false,
          screen.$hash || null,
          screen.lied || false
        );
      }

      // 插入 Canvas 2D
      if (fingerprint.canvas2d) {
        const canvas = fingerprint.canvas2d;
        this.db.prepare(`
          INSERT INTO canvas (
            fingerprint_id, canvas_type, data_uri, paint_uri, text_uri, emoji_uri,
            text_metrics_system_sum, emoji_set, mods, hash, lied, lied_text_metrics
          ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        `).run(
          fingerprintId,
          '2d',
          canvas.dataURI || null,
          canvas.paintURI || null,
          canvas.textURI || null,
          canvas.emojiURI || null,
          canvas.textMetricsSystemSum || null,
          JSON.stringify(canvas.emojiSet || []),
          canvas.mods || null,
          canvas.$hash || null,
          canvas.lied || false,
          canvas.liedTextMetrics || false
        );
      }

      // 插入 WebGL
      if (fingerprint.canvasWebgl) {
        const webgl = fingerprint.canvasWebgl;
        this.db.prepare(`
          INSERT INTO webgl (
            fingerprint_id, data_uri, data_uri2, extensions, parameters_json,
            gpu_compressed, gpu_brand, gpu_confidence, pixels_hash, pixels2_hash,
            hash, lied, parameter_or_extension_lie
          ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        `).run(
          fingerprintId,
          webgl.dataURI || null,
          webgl.dataURI2 || null,
          JSON.stringify(webgl.extensions || []),
          JSON.stringify(webgl.parameters || {}),
          webgl.gpu?.compressedGPU || null,
          webgl.gpu?.brand || null,
          webgl.gpu?.confidence || null,
          webgl.pixels || null,
          webgl.pixels2 || null,
          webgl.$hash || null,
          webgl.lied || false,
          webgl.parameterOrExtensionLie || false
        );
      }

      // 插入 Timezone
      if (fingerprint.timezone) {
        const tz = fingerprint.timezone;
        this.db.prepare(`
          INSERT INTO timezone (
            fingerprint_id, zone, offset, offset_computed, location,
            location_measured, location_epoch, hash, lied
          ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        `).run(
          fingerprintId,
          tz.zone || null,
          tz.offset || null,
          tz.offsetComputed || null,
          tz.location || null,
          tz.locationMeasured || null,
          tz.locationEpoch || null,
          tz.$hash || null,
          tz.lied || false
        );
      }

      // 插入 Fonts
      if (fingerprint.fonts) {
        const fonts = fingerprint.fonts;
        this.db.prepare(`
          INSERT INTO fonts (
            fingerprint_id, font_face_load_fonts, platform_version,
            emoji_set, pixel_size_system_sum, hash, lied
          ) VALUES (?, ?, ?, ?, ?, ?, ?)
        `).run(
          fingerprintId,
          JSON.stringify(fonts.fontFaceLoadFonts || []),
          fonts.platformVersion || null,
          JSON.stringify(fonts.emojiSet || []),
          fonts.pixelSizeSystemSum || null,
          fonts.$hash || null,
          fonts.lied || false
        );
      }

      // 插入 Audio
      if (fingerprint.offlineAudioContext) {
        const audio = fingerprint.offlineAudioContext;
        this.db.prepare(`
          INSERT INTO audio (
            fingerprint_id, sample_sum, total_unique_samples,
            float_frequency_data_sum, float_time_domain_data_sum,
            compressor_gain_reduction, bins_sample, copy_sample,
            noise, hash, lied
          ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        `).run(
          fingerprintId,
          audio.sampleSum || null,
          audio.totalUniqueSamples || null,
          audio.floatFrequencyDataSum || null,
          audio.floatTimeDomainDataSum || null,
          audio.compressorGainReduction || null,
          audio.binsSample || null,
          audio.copySample || null,
          audio.noise || null,
          audio.$hash || null,
          audio.lied || false
        );
      }

      // 插入 Resistance
      if (fingerprint.resistance) {
        const res = fingerprint.resistance;
        this.db.prepare(`
          INSERT INTO resistance (
            fingerprint_id, privacy, security, mode, extension, engine, hash
          ) VALUES (?, ?, ?, ?, ?, ?, ?)
        `).run(
          fingerprintId,
          res.privacy || null,
          res.security || null,
          res.mode || null,
          res.extension || null,
          res.engine || null,
          res.$hash || null
        );
      }

      // 插入 Headless
      if (fingerprint.headless) {
        const hl = fingerprint.headless;
        this.db.prepare(`
          INSERT INTO headless (
            fingerprint_id, chromium, headless_rating,
            like_headless_rating, stealth_rating, platform_estimate, hash
          ) VALUES (?, ?, ?, ?, ?, ?, ?)
        `).run(
          fingerprintId,
          hl.chromium || false,
          hl.headlessRating || null,
          hl.likeHeadlessRating || null,
          hl.stealthRating || null,
          JSON.stringify(hl.platformEstimate || []),
          hl.$hash || null
        );
      }

      // 插入 Lies
      if (fingerprint.lies) {
        const lies = fingerprint.lies;
        this.db.prepare(`
          INSERT INTO lies (
            fingerprint_id, total_lies, lies_json, hash
          ) VALUES (?, ?, ?, ?)
        `).run(
          fingerprintId,
          lies.totalLies || 0,
          JSON.stringify(lies.data || {}),
          lies.$hash || null
        );
      }

      // 插入完整 JSON 數據（備份）
      const insertData = this.db.prepare(`
        INSERT INTO fingerprint_data (fingerprint_id, data_type, data_json)
        VALUES (?, ?, ?)
      `);

      insertData.run(fingerprintId, 'fingerprint', JSON.stringify(fingerprint));
      insertData.run(fingerprintId, 'creep', JSON.stringify(creep));

      return fingerprintId;
    });

    return transaction();
  }

  /**
   * 獲取統計信息
   */
  getStats() {
    if (!this.db) {
      throw new Error('數據庫未連接');
    }

    const total = this.db.prepare('SELECT COUNT(*) as count FROM fingerprints').get();
    const byPrivacy = this.db.prepare(`
      SELECT privacy, COUNT(*) as count
      FROM resistance
      GROUP BY privacy
    `).all();
    const byEngine = this.db.prepare(`
      SELECT engine, COUNT(*) as count
      FROM resistance
      GROUP BY engine
    `).all();

    return {
      total: total.count,
      byPrivacy,
      byEngine
    };
  }

  /**
   * 關閉數據庫連接
   */
  close() {
    if (this.db) {
      this.db.close();
      this.db = null;
      console.log('✓ 數據庫連接已關閉');
    }
  }
}


