package config

import (
	"fmt"
	"os"

	"github.com/spf13/viper"
)

type Config struct {
	Server   ServerConfig   `mapstructure:"server"`
	Database DatabaseConfig `mapstructure:"database"`
	Redis    RedisConfig    `mapstructure:"redis"`
	Kafka    KafkaConfig    `mapstructure:"kafka"`
	Log      LogConfig      `mapstructure:"log"`
}

type ServerConfig struct {
	Port         int    `mapstructure:"port"`
	Mode         string `mapstructure:"mode"` // debug, release
	ReadTimeout  int    `mapstructure:"read_timeout"`
	WriteTimeout int    `mapstructure:"write_timeout"`
	MaxConns     int    `mapstructure:"max_conns"`
}

type DatabaseConfig struct {
	Host            string `mapstructure:"host"`
	Port            int    `mapstructure:"port"`
	User            string `mapstructure:"user"`
	Password        string `mapstructure:"password"`
	DBName          string `mapstructure:"dbname"`
	MaxOpenConns    int    `mapstructure:"max_open_conns"`
	MaxIdleConns    int    `mapstructure:"max_idle_conns"`
	ConnMaxLifetime int    `mapstructure:"conn_max_lifetime"` // seconds
}

type RedisConfig struct {
	Host         string `mapstructure:"host"`
	Port         int    `mapstructure:"port"`
	Password     string `mapstructure:"password"`
	DB           int    `mapstructure:"db"`
	PoolSize     int    `mapstructure:"pool_size"`
	MinIdleConns int    `mapstructure:"min_idle_conns"`
}

type KafkaConfig struct {
	Brokers      []string `mapstructure:"brokers"`
	Topic        string   `mapstructure:"topic"`
	GroupID      string   `mapstructure:"group_id"`
	BatchSize    int      `mapstructure:"batch_size"`
	BatchTimeout int      `mapstructure:"batch_timeout"` // milliseconds
}

type LogConfig struct {
	Level      string `mapstructure:"level"`       // debug, info, warn, error
	OutputPath string `mapstructure:"output_path"` // stdout, file path
	MaxSize    int    `mapstructure:"max_size"`    // MB
	MaxBackups int    `mapstructure:"max_backups"`
	MaxAge     int    `mapstructure:"max_age"` // days
}

var GlobalConfig *Config

func LoadConfig(configPath string) (*Config, error) {
	viper.SetConfigType("yaml")
	
	if configPath != "" {
		viper.SetConfigFile(configPath)
	} else {
		viper.SetConfigName("config")
		viper.AddConfigPath("./configs")
		viper.AddConfigPath("../configs")
		viper.AddConfigPath("../../configs")
	}

	// 環境變數覆蓋
	viper.AutomaticEnv()

	// 讀取配置文件
	if err := viper.ReadInConfig(); err != nil {
		return nil, fmt.Errorf("讀取配置文件失敗: %w", err)
	}

	var config Config
	if err := viper.Unmarshal(&config); err != nil {
		return nil, fmt.Errorf("解析配置文件失敗: %w", err)
	}

	// 環境變數覆蓋特定值
	if port := os.Getenv("SERVER_PORT"); port != "" {
		viper.Set("server.port", port)
	}
	if dbHost := os.Getenv("DB_HOST"); dbHost != "" {
		viper.Set("database.host", dbHost)
	}
	if redisHost := os.Getenv("REDIS_HOST"); redisHost != "" {
		viper.Set("redis.host", redisHost)
	}

	GlobalConfig = &config
	return &config, nil
}

func GetConfig() *Config {
	return GlobalConfig
}

