# NanoBananaBatchPy

批量检测和移除图片中的 Nano Banana 水印工具

## 项目介绍

NanoBananaBatchPy 是一个专门用于批量检测和移除图片中 Nano Banana 水印的Python工具。它能够自动扫描目录中的图片文件，检测水印存在，并通过图像处理技术移除水印，同时保持图片的原始质量。

## 功能特性

- 批量处理：自动扫描目录中的所有图片文件
- 智能检测：使用掩码技术准确识别 Nano Banana 水印
- 水印移除：通过反Alpha混合技术移除水印
- 多种格式支持：支持 PNG、JPG、JPEG、WebP 格式
- 详细日志：生成处理日志，记录处理结果
- 安全处理：处理后直接覆盖原文件，保持文件结构不变

## 系统要求

- Python 3.6+
- Pillow (图像处理库)

## 安装步骤

1. **克隆仓库**
   ```bash
   git clone https://github.com/w243420707/NanoBananaBatchPy.git
   cd NanoBananaBatchPy
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements-python.txt
   ```

## 使用方法

### 方法一：直接运行批处理文件

1. 双击 `run_nano_banana_batch.bat` 文件
2. 程序会自动扫描当前目录及其子目录中的图片文件
3. 处理完成后，会在当前目录生成处理日志

### 方法二：通过命令行运行

1. 打开命令行终端
2. 导航到项目目录
3. 运行以下命令：
   ```bash
   python nano_banana_batch.py
   ```

## 工作原理

1. **扫描目录**：程序会扫描当前目录及其子目录，寻找支持的图片文件
2. **加载掩码**：加载预定义的水印检测掩码（48x48 和 96x96 两种尺寸）
3. **水印检测**：使用掩码在图片右下角检测水印
4. **水印移除**：对检测到水印的图片执行反Alpha混合操作，移除水印
5. **保存结果**：直接覆盖原文件，并生成处理日志

## 项目结构

```
NanoBananaBatchPy/
├── nano_banana_batch.py    # 主脚本
├── run_nano_banana_batch.bat  # 运行批处理文件
├── requirements-python.txt     # 依赖文件
├── public/
│   └── assets/
│       ├── mask_48.png     # 小尺寸水印检测掩码
│       └── mask_96.png     # 大尺寸水印检测掩码
└── README.md               # 项目说明文档
```

## 注意事项

1. 程序会直接覆盖原文件，请确保在处理前备份重要图片
2. 仅支持检测和移除 Nano Banana 水印，不支持其他类型的水印
3. 对于分辨率过低的图片，可能无法准确检测水印
4. 处理后会在当前目录生成 `NanoBananaBatchRemover.log` 日志文件

## 处理结果说明

- **成功清理**：图片中存在 Nano Banana 水印并已成功移除
- **跳过无水印**：图片中未检测到 Nano Banana 水印
- **处理失败**：处理过程中出现错误，详细信息会记录在日志中

## 示例输出

```
扫描目录: C:\Path\To\NanoBananaBatchPy
发现图片: 10 张
[1/10] 处理中: images\photo1.jpg
    -> 已覆盖 photo1.jpg
[2/10] 处理中: images\photo2.png
    -> 未检测到 Nano Banana 水印
...
处理完成
成功清理: 5
跳过无水印: 4
处理失败: 1
日志文件: C:\Path\To\NanoBananaBatchPy\NanoBananaBatchRemover.log
```

## 依赖项

- Pillow：用于图像处理

## 许可证

本项目采用 MIT 许可证

## 贡献

欢迎提交 Issue 和 Pull Request 来改进这个项目！

## 联系方式

如果您有任何问题或建议，请通过 GitHub Issues 联系我们。