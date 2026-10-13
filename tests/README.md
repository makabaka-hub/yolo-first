# 结构回归检查

检查模块导入无副作用、前后端依赖边界、事件的发布与取消订阅、第三方输出转发不阻塞 UI 进度、独立预测不触发训练，以及错误参数在计算开始前被拒绝。

在项目根目录运行：

```text
.\.venv\Scripts\python.exe -X utf8 -m unittest discover -s tests -v
```

这些检查不训练模型。实际训练和图片预测仍需单独运行，工程记录见 `logs/progress.md`。
