import uiautomator2 as u2
import pprint
import os
import json
import xmltodict
import time
import os
import openai
import tkinter as tk
from tkinter import filedialog
import re

import json
import requests
from openai import OpenAI
from zhipuai import ZhipuAI

base_url = "http://lab.georgechen.top:8000/v1/"
client = ZhipuAI(api_key="EMP.TY", base_url=base_url)


def request_post(url, param):
    # print(url)
    # print(param)
    # data={"prompt":"This is a my movie app, in its search movie page, the input category is query category. This input is about your favorite move in this year. Please search themovie, the movie is"}
    data = {"prompt": param}
    headers = {'content-type': 'application/json'}
    text = ""
    ret = requests.post(url, json=data, headers=headers, timeout=10)
    print(ret.status_code)
    if ret.status_code == 200:
        text = json.loads(ret.text)["response"]
        print(text)

    return text

import re

def extract_first_quote(text):
    # 正则表达式匹配第一个英文双引号、单引号、括号或中文双引号内的内容
    match = re.search(r'["\‘\’\“\”](.*?)["\‘\’\“\”]|\((.*?)\)', text)
    if match:
        # 检查哪个分组有匹配的内容
        for i in range(1, 3):
            if match.group(i):
                content = match.group(i)
                # 如果内容中有"et"字符，则搜索第二个引号或括号的内容
                if 'et' in content:
                    second_match = re.search(r'["\‘\’\“\”](.*?)["\‘\’\“\”]|\((.*?)\)', text[match.end():])
                    if second_match:
                        for j in range(1, 3):
                            if second_match.group(j):
                                return second_match.group(j)
                return content
    else:
        return text



def simple_chat(prompt,use_stream=False):
    messages = [
        {
            "role": "system",
            "content": "You are ChatGLM3, a large language model trained by Zhipu.AI. Follow "
                       "the user's instructions carefully. Respond using markdown.",
        },
        {
            "role": "user",
            "content": prompt
        }
    ]
    response = client.chat.completions.create(
        model="chatglm3_",
        messages=messages,
        stream=use_stream,
        max_tokens=256,
        temperature=0.8,
        top_p=0.8)
    if response:
        content = response.choices[0].message.content
    else:
        content = "error!"
    return content

def openai_chat(prom):
    # client = OpenAI(
    #     # This is the default and can be omitted
    #     api_key="sk-kyGurrvVkSjA6OS54619603d700340F4Bd190676392f7428",
    # )
    #
    # chat_completion = client.chat.completions.create(
    #     messages=[
    #         {
    #             "role": "user",
    #             "content": prom,
    #         }
    #     ],
    #     model="gpt-3.5-turbo",
    # )
    # return chat_completion
    client = OpenAI(
        base_url="https://api.gpts.vin/v1",
        api_key="sk-kyGurrvVkSjA6OS54619603d700340F4Bd190676392f7428"
    )

    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prom}
        ]
    )

    return completion.choices[0].message.content


def getAllComponents(jsondata: dict):

    root = jsondata['hierarchy']

    queue = [root]
    res = []

    while queue:
        currentNode = queue.pop(0)
        if 'node' in currentNode:
            if type(currentNode['node']).__name__ == 'dict':
                queue.append(currentNode['node'])
            else:
                for e in currentNode['node']:
                    queue.append(e)
        else:
            if ('com.android.systemui' not in currentNode['@resource-id']) and (
                    'com.android.systemui' not in currentNode['@package']):
                res.append(currentNode)

    return res


def find_EditText(jsondata: dict):

    all_components = getAllComponents(jsondata)
    print("allComponentData"+str(all_components))
    ans = []

    for e_component in all_components:
        if '@class' in e_component and (e_component['@class'] == 'android.widget.EditText' or e_component['@class'] == 'android.widget.AutoCompleteTextView'):
            ans.append(e_component)
    return ans


def get_basic_info(e_component: dict):

    key_list = ['id', 'text', 'label', 'text-hint', 'app_name']
    key_at_list = ['resource-id', 'text', 'label', 'content-desc', 'package']
    dict_info = {}

    for i in range(len(key_list)):
        dict_info[key_list[i]] = None
        for e_property in e_component:
            if key_at_list[i] in e_property.lower():
                dict_info[key_list[i]] = e_component[e_property]
                break

    return dict_info


def chooseFromPos(all_components: list, bounds: list):

    
    same_horizon_components = []
    same_vertical_components = []

    for e_component in all_components:
        e_bounds = e_component['@bounds']
        if e_bounds == bounds:
            continue
        if (e_bounds[1], e_bounds[3]) == (bounds[1], bounds[3]):
            same_horizon_components.append(e_component)
        if (e_bounds[0], e_bounds[2]) == (bounds[0], bounds[2]):
            same_vertical_components.append(e_component)

    return same_horizon_components, same_vertical_components


def turn_null_to_str(prop: str):

    if prop == None:
        return ''
    else:
        return prop


def component_basic_info(jsondata: dict):

    text_id = "The purpose of this component may be '<EditText id>'. "
    text_label = "The label of this component is '<label>'. "
    text_text = "The text on this component is '<text>'. "
    text_hint = "The hint text of this component is '<hint>'. "

    if jsondata['id'] == "" or jsondata['id'] == None:
        text_id = ""
    else:
        EditText_id = jsondata['id'].split('/')[-1]
        EditText_id = EditText_id.replace('_', ' ')
        text_id = text_id.replace('<EditText id>', EditText_id)

    if jsondata['label'] == "" or jsondata['label'] == None:
        text_label = ""
    else:
        label = jsondata['label']
        text_label = text_label.replace('<label>', label)

    if jsondata['text'] == "" or jsondata['text'] == None:
        text_text = ""
    else:
        text = jsondata['text']
        text_text = text_text.replace('<text>', text)

    if jsondata['text-hint'] == "" or jsondata['text-hint'] == None:
        text_hint = ""
    else:
        hint = jsondata['text-hint']
        text_hint = text_hint.replace('<hint>', hint)

    return text_id + text_label + text_text + text_hint + '\n'


def isEnglish(s: str):

    s = s.replace('\u2026', '')
    return s.isascii()


def use_context_info_generate_prompt(jsondata: dict):
    print(jsondata)
    text_header = "Question: "
    text_app_name = "This is a <app name> app. "
    text_activity_name = "On its page, it has an input component. "
    text_label = "The label of this component is '<label>'. "
    text_text = "The text on this component is '<text>'. "
    text_context_info = "Below is the relevant prompt information of the input component:\n<context information>"
    text_id = "The purpose of this input component may be '<EditText id>'. "
    # text_ask = "What is the hint text of this input component?\n"
    text_ask = "If I want to test the input field, what should I type?(Please type my most likely by using a specific example instead of giving vague suggestions.Don't output words like 'you should type', just output specific things rather than a general category.Please spread your thinking and do not copy the text on this component.)\n"
    #text_ask = "If I want to test the input field, what should I type?(Just provide a brief answer without any further explanation)\n"
    app_name = jsondata['app_name'].split('.')[-1]
    text_app_name = text_app_name.replace('<app name>', app_name)

    if jsondata['label'] == "" or jsondata['label'] == None:
        text_label = ""
    else:
        label = jsondata['label']
        text_label = text_label.replace('<label>', label)

    if jsondata['text'] == "" or jsondata['text'] == None:
        text_text = ""
    else:
        text = jsondata['text']
        text_text = text_text.replace('<text>', text)

    context_info = ""
    if len(jsondata['same-horizon']) > 0:
        for e in jsondata['same-horizon']:
            # if not isEnglish(turn_null_to_str(e['label']) + turn_null_to_str(e['text']) + turn_null_to_str(
            #         e['text-hint'])):
            #     continue
            context_info += "There is a component on the same horizontal line as this input component. "
            context_info += component_basic_info(e)

    if len(jsondata['same-vertical']) > 0:
        for e in jsondata['same-vertical']:
            # if not isEnglish(turn_null_to_str(e['label']) + turn_null_to_str(e['text']) + turn_null_to_str(
            #         e['text-hint'])):
            #     continue
            context_info += "There is a component on the same vertical line as this input component. "
            context_info += component_basic_info(e)

    if len(jsondata['same-horizon']) > 0 or len(jsondata['same-vertical']) > 0:
        text_context_info = text_context_info.replace('<context information>', context_info)
    else:
        text_context_info = ""

    if jsondata['id'] == "" or jsondata['id'] == None:
        text_id = ""
    else:
        EditText_id = jsondata['id'].split('/')[-1]
        EditText_id = EditText_id.replace('_', ' ')
        text_id = text_id.replace('<EditText id>', EditText_id)


    question = text_header + text_app_name + text_activity_name + text_label + text_text + text_context_info + text_id + text_ask
    # question = text_header + text_app_name + text_activity_name + text_label + text_context_info + text_id + text_ask
    final_text = question

    return final_text


def show_hint(res: list, hint_text: str):
    x1 = int(res[0])
    y1 = int(res[1])
    x2 = int(res[2])
    y2 = int(res[3])
    h = y2 - y1
    w = x2 - x1
    if h < 100:
        y2 = y1 + 100
    hint_text = hint_text.replace(' ', '-')
    cmd = "adb shell am startservice -n dongzhong.testforfloatingwindow/.FloatingButtonService -e x1 {x1} -e y1 {y1} -e x2 {x2} -e y2 {y2} -e text {text}"
    cmd = cmd.replace('{x1}', str(x1)).replace('{y1}', str(y1)).replace('{x2}', str(x2)).replace('{y2}',
                                                                                                 str(y2)).replace(
        '{text}', hint_text)
    print(cmd)
    os.system(cmd)


def insert_code(e_id: str, hint_text: str, f_path: str):
    e_id = e_id + '"'
    fr = open(f_path, 'r', encoding='utf-8')
    print('Reading hierarchy tree...')
    pprint.pprint(fr)
    lines = []
    empty_cnt = 0
    idx = 0
    add_idx = True
    for e_line in fr:
        lines.append(e_line)
        if (e_id in e_line):
            add_idx = False
            empty_cnt = e_line.find('a')
        if (add_idx):
            idx += 1
    fr.close()

    print('idx: ' + str(idx))

    print('empty cnt: ' + str(empty_cnt))
    add_content = ' ' * empty_cnt + 'android:hint="' + hint_text + '"\n'
    lines.insert(idx + 1, add_content)
    s = ''.join(lines)
    fw = open(f_path, 'w', encoding='utf-8')
    fw.write(s)
    fw.close()
    win32api.MessageBox(0,
                        "You forget to add hint in EditText! \nPredicted hint text is added automatically in line " + str(
                            idx + 2), "Attention", win32con.MB_YESNO)



# while True:
print('Connect to device...')
d = u2.connect()
print('Device connected.')
# print(d.info)
page_source = d.dump_hierarchy(compressed=True, pretty=True)
# print(page_source)
save_path = r"D:\pycharmprojects\QTypist\example\10-get-context-info-in-ui-tree"
xml_file = open(save_path + 'hierarchy.xml', 'w', encoding='utf-8')
xml_file.write(page_source)
xml_file.close()
xml_file = open(save_path + 'hierarchy.xml', 'r', encoding='utf-8')
print('Reading hierarchy tree...')
data_dict = xmltodict.parse(xml_file.read())
print(data_dict)



# root = tk.Tk()
# root.withdraw()
# path = filedialog.askopenfilename()
# print(path)
# with open(path, "r", encoding="UTF-8") as f:
#     #读取文件数据
#     data_dict = json.load(f)
# print(data_dict)

all_components = getAllComponents(data_dict)

print('All components nums:' + str(len(all_components)))

components_with_edit_text = find_EditText(data_dict)

print('EditText components nums:' + str(len(components_with_edit_text)))

no_hint_text = []

for e in components_with_edit_text:
    if e['@content-desc'] == '':
        no_hint_text.append(e)

print('EditText with no hint nums:' + str(len(no_hint_text)))

f_path = ''

# if len(no_hint_text) != 0:
#     msg = """
#             """
    # ret = win32api.MessageBox(0, msg, "Attention", win32con.MB_YESNO)
    # if ret == 7:
    #     time.sleep(3)
    #     continue
    # root = tk.Tk()
    # root.withdraw()
    # f_path = filedialog.askopenfilename()

for e_component in no_hint_text:
    print('---------------')
    pprint.pprint(e_component)
    print('---------------')
    bounds = e_component['@bounds']
    dict_info = get_basic_info(e_component)

    (same_horizon_components, same_vertical_components) = chooseFromPos(all_components, bounds)
    dict_info['same-horizon'] = []
    dict_info['same-vertical'] = []
    for e_hor_component in same_horizon_components:
        dict_info['same-horizon'].append(get_basic_info(e_hor_component))
    for e_ver_component in same_vertical_components:
        dict_info['same-vertical'].append(get_basic_info(e_ver_component))
    dict_info['activity_name'] = ''
    pprint.pprint("dict_info"+str(dict_info))
    final_text = use_context_info_generate_prompt(dict_info)
    print(final_text)
    # url = "http://lab.georgechen.top:8000"
    mid_output = simple_chat(final_text,use_stream=False)
    #mid_output = openai_chat(final_text)
    print(mid_output)
    output = extract_first_quote(mid_output)
    print(output)
    print(output.split("\""))
    # chatglm数据输出处理
    print(output)
    print('We think you should use (' + output + ') as hint text.')
    real_ans = output
    # real_ans = output.split("\"")[1][:-1]
    # print('We think you should use (' + real_ans + ') as hint text.')
    # print('We think you should use (' + output + ') as hint text.')
    res = []
    bounds = e_component['@bounds']
    bounds = bounds.split(',')
    print(bounds)
    res.append(bounds[0].replace('[', ''))
    mid = bounds[1].split('][')
    res.append(mid[0])
    res.append(mid[1])
    res.append(bounds[2].replace(']', ''))
    print(res)
    show_hint(res, real_ans)
    # e_id = e_component['@resource-id']
    # e_id = e_id.split('/')[-1]
    # print(e_id)
    # insert_code(e_id, real_ans, f_path)
    time.sleep(3)
#  chat-glm llama2

