-- ============================================
-- MSSQL 學習環境初始化
-- 建立練習用資料庫與基本資料表
-- ============================================

-- 建立練習資料庫
IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'LearningDB')
BEGIN
    CREATE DATABASE LearningDB;
    PRINT 'LearningDB 建立完成';
END
GO

USE LearningDB;
GO

-- 建立員工資料表
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Employees')
BEGIN
    CREATE TABLE Employees (
        EmployeeID   INT PRIMARY KEY IDENTITY(1,1),
        FirstName    NVARCHAR(50)  NOT NULL,
        LastName     NVARCHAR(50)  NOT NULL,
        Email        NVARCHAR(100) UNIQUE,
        Department   NVARCHAR(50),
        Salary       DECIMAL(10,2),
        HireDate     DATE          DEFAULT GETDATE(),
        IsActive     BIT           DEFAULT 1
    );
    PRINT 'Employees 資料表建立完成';
END
GO

-- 插入範例資料
INSERT INTO Employees (FirstName, LastName, Email, Department, Salary, HireDate)
VALUES
    (N'志明',   N'陳', 'chihming.chen@example.com',  N'工程部', 85000, '2021-03-15'),
    (N'美華',   N'林', 'meihua.lin@example.com',     N'行銷部', 72000, '2020-07-01'),
    (N'大衛',   N'王', 'david.wang@example.com',     N'工程部', 95000, '2019-11-20'),
    (N'小玲',   N'張', 'xiaoling.zhang@example.com', N'人資部', 68000, '2022-01-10'),
    (N'建國',   N'李', 'jianguo.li@example.com',     N'工程部', 91000, '2018-05-30');
GO

PRINT '初始化完成！執行 SELECT * FROM Employees 確認資料。';
