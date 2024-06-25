# Python
from openai import OpenAI
import os
import fnmatch

DOCC = f"Guide"

client = OpenAI(
    base_url='http://localhost:11434/v1/',

    # required but ignored
    api_key='ollama',
)

# - 每句勿超過30字。
SYSTEM_PROMPT="""
你是一位專業且文學素養豐富的台灣翻譯專家。

請按照以下規則翻譯為台灣繁體中文：

- 只傳回翻譯完成的文本，不做任何解釋。
- 語言：用繁體中文和台灣慣用語翻譯，勿使用簡體中文和中國慣用語。
- 風格：符合台灣人寫作習慣，通順易讀，並力求文學性及雋永。
- 名詞：用台灣慣用譯法翻譯電影名稱，書名、作者、藝人名。同一篇文章內的名詞翻譯需保持一致。
- 格式：所有標點符號必須為全形，中英文之間保持空格。
- 避免倒裝句。
- 輸入的文本為 Markdown，如果遇到程式碼區塊，則保留原文

開始： 
"""

mds = [
    'CompleteChecking.md',
    'MigrationGuide.md',
    'RuntimeBehavior.md',
    'Swift6Mode.md',
]
largetMds = [
    'CommonProblems.md',
    'DataRaceSafety.md',
    'IncrementalAdoption.md',
]

def find_md_files(root_dir: str) -> list[str]:
    md_files = []
    for root, dirs, files in os.walk(root_dir):
        for file in fnmatch.filter(files, '*.md'):
            md_files.append(os.path.join(root, file))
    return md_files

def readFileLine(file: str) -> list[str]:
    with open(file, 'r', encoding='utf-8') as file:
        return file.readlines()
    
def classify(input: list[str], symbol: str) -> list[str]:
    result = []
    current_group = []

    for line in input:
        if line.startswith(symbol):
            if current_group:
                result.append("".join(current_group))
                current_group = []
        current_group.append(line)
    
    if current_group:
        result.append("".join(current_group))

    return result

def readFile(file: str) -> str:
    with open(file, 'r', encoding='utf-8') as file:
        # Read the entire file
        return file.read()
    
def writeFile(file: str, content: str) -> str:
    with open(file, 'w', encoding='utf-8') as file:
        return file.write(content)
    
def translate(content: str) -> str: 
    chat_completion = client.chat.completions.create(
        messages=[
            {'role': 'system', 'content': SYSTEM_PROMPT},
            {
                'role': 'user',
                'content': content,
            }
        ],
        model='llama3',
    )
    translated = chat_completion.choices[0].message.content
    return translated

def mkdir(dir_name: str) -> bool:
    try: 
        os.mkdir(dir_name)
        return True
    except:
        return True

def start(path: str, lang: str):
    origin = f'{path}.docc'
    target = f'{path}{lang}.docc'

    if os.mkdir(target) is False:
        return

    
    mds = find_md_files(origin)
    
    for path in mds:
        md = path.split(f"{origin}/")[-1]
        fromMd = f"{origin}/{md}"
        toMd = f"{target}/{md}"

        print(f"[Read] {md}")
        lines = readFileLine(fromMd)
        groups = classify(lines, '#')

        print(f"[Translate] {md}")
        translates = [translate(text) for text in groups]

        print(f"[Write] {md}")
        writeFile(toMd, "\n\n".join(translates))

start(DOCC, 'ZH')