import json
import os
import glob

recipes = open("recipes", "w")

d=dict()
path = r'C:\Users\Ananth\Desktop\recipes'
for filename in glob.glob(os.path.join(path, '*.json')):
   with open(os.path.join(os.getcwd(), filename), 'r') as f: # open in readonly mode
       data = json.load(f)
       # if data['type']=='minecraft:crafting_shaped' or data['type']=='minecraft:crafting_shapeless':
       items=[]
       try:
           print(data['result'])
       except:
           continue;
       if 'key' in data:
           pattern=''.join(data['pattern'])
           for k,i in data['key'].items():
                if type(i) is dict:
                    for c in range(0,pattern.count(k)):
                        items.append(list(i.values())[0][10:])
       if 'ingredients' in data:
           for i in data['ingredients']:
                if type(i) is dict:
                    items.append(list(i.values())[0][10:])
                if type(i) is list:
                    for j in i:
                        items.append(list(j.values())[0][10:])
       if 'ingredient' in data:
           for i in data['ingredient']:
                if type(i) is dict:
                    items.append(list(i.values())[0][10:])
                if type(i) is list:
                    for j in i:
                        items.append(list(j.values())[0][10:])
       if type(data['result']) is dict:
           if data['result']['item'][10:] in d:
               continue
           d[data['result']['item'][10:]]=items
       elif type(data['result']) is str:
           if data['result'][10:] in d:
               continue
           d[data['result'][10:]]=items

recipe=dict()
for k,v in d.items():
    v2=set(v)
    recipe[k]=[]
    for i in v2:
        recipe[k].append((i,v.count(i)))
print(recipe)
recipes.write(str(recipe))