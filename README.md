# AI-MapBook

## 项目活动

Datawhale AI 夏令营😀

## 项目介绍

![image](https://github.com/user-attachments/assets/0dee61ff-f80b-47ca-b02c-fa0c768752ae)


AI-MapBook 是一个利用LLM技术为故事讲述提供地图支持的项目。它通过大型语言模型（LLM）从书籍中提取地理信息和属性信息，结合地理编码得到地理坐标数据，并在交互式地图上进行可视化展示，为读者提供沉浸式的故事探索体验。该项目适用于故事创作者、教育工作者和地图爱好者，通过结合人工智能和地理空间技术，增强叙事效果。

[在线体验](https://ai-mapbook-zasfamyfxydadn2x8qyros.streamlit.app/)
[演示视频](https://www.bilibili.com/video/BV1HpaoeTEST/?vd_source=e7e7a9aa0f8778cf8fc1a51dded02077)

## 应用场景

- 考古分析
- 地理历史学习
- 军事情报检索
- 社交网络分析

## 技术栈

- **后端**: python原生
- **前端**: Streamlit

## 主要思路

![image](https://github.com/user-attachments/assets/08ef18dc-7cac-4681-9558-d291b184c2c6)


1. **数据提取🏆**: 使用LLM从故事书籍中提取地理信息和属性信息。
2. **数据处理🏆**: 将提取的事件信息进行处理得到地理坐标，以便在前端进行展示。
3. **地图可视化🏆**: 利用Leaflet在前端展示交互式地图，并在地图上标记提取的坐标点。
4. **用户交互🏆**: 提供用户界面，允许用户浏览和探索故事中的地理信息。
5. **RAG问答🎯**：通过对用户上传的PDF或TXT文件进行向量化检索存储，并使用RAG模型进行问答，实现故事中地理信息的查询和展示。
6. **用户意图识别🎯**: 通过一个意图识别Agent来提取用户意图，进而创建交互模板，构建地图，支持内容导出文件（开发中）。
## 项目结构

```
AI-MapBook/
├── app.py
├── requirements.txt
├── install.py
├── models
├── storage
├── data
├──utils
│    └── __init__.py
│    └── geocode_utils.py
│    └── model_back.py
│    └── text_processing.py
│    └── map.py
│    └── rag.py
|.env_example
├── LICENSE
├── README.md
```

## 安装与启动
> 项目部署推荐使用全局科学环境！！！😉😉
> 推荐使用在线[API](https://platform.deepseek.com/usage)
1. 进入项目目录：
   ```sh
   cd AI-MapBook
   ```

2. 配置环境及安装依赖：
   ```sh
   conda create --name map-book python=3.10.13
   conda activate map-book
   pip install -r requirements.txt 
   python install.py
   ```
   > 配置模型设置：下载模型权重后，通过修改config.json的以下代码片段来修改模型输入输出上下文长度：
   ```json
    {
        "architectures": [
            "Qwen2ForCausalLM"
        ],
        // ...
        "vocab_size": 152064,

        // adding the following snippets
        "rope_scaling": {
            "factor": 4.0,
            "original_max_position_embeddings": 32768,
            "type": "yarn"
        }
    }

   > 如果需要本地部署,请在requirements.txt文件中添加:
   ```bash
   llama-index-llms-ipex-llm
   ```
   ```

3. 启动后端服务：
   ```sh
   streamlit run app.py
   ```
   

## 贡献

我们欢迎任何形式的贡献，包括但不限于代码提交、问题反馈、功能建议等。

## 许可证

本项目采用 [GNU Affero General Public License (AGPL)](LICENSE)。

---
