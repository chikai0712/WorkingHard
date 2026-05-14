package logger

import (
	"os"
	"go.uber.org/zap"
	"go.uber.org/zap/zapcore"
)

func InitSimpleLogger() {
	config := zap.NewProductionConfig()
	config.EncoderConfig.TimeKey = "timestamp"
	config.EncoderConfig.EncodeTime = zapcore.ISO8601TimeEncoder
	config.EncoderConfig.EncodeLevel = zapcore.LowercaseLevelEncoder
	
	Logger, _ = config.Build(zap.AddCaller(), zap.AddStacktrace(zapcore.ErrorLevel))
}

func GetSimpleLogger() *zap.Logger {
	if Logger == nil {
		InitSimpleLogger()
	}
	return Logger
}

