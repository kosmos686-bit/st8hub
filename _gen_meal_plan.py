# -*- coding: utf-8 -*-
import json, copy, os, sys
sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

BREAKFASTS = [
    {"id":"breakfast","time":"08:00","emoji":"🌅",
     "display":"Омлет 3яйца + хлеб ржаной 60g + апельсин","drink":"кофе",
     "items":["Яйца 3шт","Хлеб ржаной 60g","Апельсин 1шт"],
     "kcal":460,"protein":38,"carbs":44,"fat":16},
    {"id":"breakfast","time":"08:00","emoji":"🌅",
     "display":"Овсянка 80g + банан + яйца 2шт вкрутую","drink":"чай",
     "items":["Овсянка 80g","Банан 1шт","Яйца 2шт"],
     "kcal":455,"protein":25,"carbs":62,"fat":12},
    {"id":"breakfast","time":"08:00","emoji":"🌅",
     "display":"Творог 5% 200g + мёд 1ч.л + яблоко","drink":"кофе",
     "items":["Творог 5% 200g","Мёд 1ч.л","Яблоко 1шт"],
     "kcal":405,"protein":36,"carbs":40,"fat":10},
    {"id":"breakfast","time":"08:00","emoji":"🌅",
     "display":"Яичница 3яйца + помидор + хлеб ржаной 60g","drink":"чай",
     "items":["Яйца 3шт","Помидор 1шт","Хлеб ржаной 60g"],
     "kcal":430,"protein":24,"carbs":32,"fat":20},
    {"id":"breakfast","time":"08:00","emoji":"🌅",
     "display":"Овсянка 80g + яблоко + орехи грецкие 20g","drink":"кофе",
     "items":["Овсянка 80g","Яблоко 1шт","Орехи грецкие 20g"],
     "kcal":480,"protein":14,"carbs":64,"fat":20},
    {"id":"breakfast","time":"08:00","emoji":"🌅",
     "display":"Омлет 3яйца + хлеб цельнозерновой 60g + грейпфрут","drink":"кофе",
     "items":["Яйца 3шт","Хлеб цельнозерновой 60g","Грейпфрут 1шт"],
     "kcal":450,"protein":26,"carbs":40,"fat":18},
    {"id":"breakfast","time":"08:00","emoji":"🌅",
     "display":"Творог 5% 200g + банан + кефир 1% 100мл","drink":"чай",
     "items":["Творог 5% 200g","Банан 1шт","Кефир 1% 100мл"],
     "kcal":430,"protein":38,"carbs":42,"fat":10},
]

SNACKS1 = [
    {"id":"snack1","time":"11:00","emoji":"🍎",
     "display":"Яблоко 1шт","drink":"вода",
     "items":["Яблоко 1шт"],"kcal":80,"protein":0,"carbs":20,"fat":0},
    {"id":"snack1","time":"11:00","emoji":"🍌",
     "display":"Банан 1шт","drink":"вода",
     "items":["Банан 1шт"],"kcal":90,"protein":1,"carbs":23,"fat":0},
    {"id":"snack1","time":"11:00","emoji":"🍊",
     "display":"Апельсин 1шт","drink":"вода",
     "items":["Апельсин 1шт"],"kcal":70,"protein":1,"carbs":17,"fat":0},
    {"id":"snack1","time":"11:00","emoji":"🍐",
     "display":"Груша 1шт","drink":"вода",
     "items":["Груша 1шт"],"kcal":85,"protein":0,"carbs":22,"fat":0},
]

LUNCHES = [
    {"id":"lunch","time":"13:30","emoji":"☀️",
     "display":"Куриная грудка 200g + рис 100g + салат огурец/помидор","drink":None,
     "items":["Куриное филе 200g","Рис 100g","Огурец 1шт","Помидор 1шт"],
     "kcal":545,"protein":54,"carbs":60,"fat":8},
    {"id":"lunch","time":"13:30","emoji":"☀️",
     "display":"Говядина 150g + гречка 100g + брокколи 200g","drink":None,
     "items":["Говядина нежирная 150g","Гречка 100g","Брокколи 200g"],
     "kcal":510,"protein":48,"carbs":54,"fat":12},
    {"id":"lunch","time":"13:30","emoji":"☀️",
     "display":"Треска 250g + картофель 150g + огурец + помидор","drink":None,
     "items":["Треска 250g","Картофель 150g","Огурец 1шт","Помидор 1шт"],
     "kcal":430,"protein":50,"carbs":38,"fat":4},
    {"id":"lunch","time":"13:30","emoji":"☀️",
     "display":"Индейка 200g + булгур 100g + помидор + огурец","drink":None,
     "items":["Индейка 200g","Булгур 100g","Помидор 1шт","Огурец 1шт"],
     "kcal":515,"protein":54,"carbs":58,"fat":8},
    {"id":"lunch","time":"13:30","emoji":"☀️",
     "display":"Куриная грудка 200g + гречка 100g + морковь тушёная 150g","drink":None,
     "items":["Куриное филе 200g","Гречка 100g","Морковь 150g"],
     "kcal":520,"protein":54,"carbs":52,"fat":8},
    {"id":"lunch","time":"13:30","emoji":"☀️",
     "display":"Минтай 300g + рис 100g + брокколи 200g","drink":None,
     "items":["Минтай 300g","Рис 100g","Брокколи 200g"],
     "kcal":455,"protein":54,"carbs":50,"fat":6},
    {"id":"lunch","time":"13:30","emoji":"☀️",
     "display":"Говядина 150g + картофель 150g + капуста тушёная 200g","drink":None,
     "items":["Говядина 150g","Картофель 150g","Капуста белокочанная 200g"],
     "kcal":500,"protein":40,"carbs":50,"fat":12},
]

SNACKS2 = [
    {"id":"snack2","time":"16:00","emoji":"🥛",
     "display":"Кефир 1% 250мл + миндаль 20g","drink":None,
     "items":["Кефир 1% 250мл","Миндаль 20g"],"kcal":250,"protein":16,"carbs":18,"fat":14},
    {"id":"snack2","time":"16:00","emoji":"🥛",
     "display":"Творог 5% 150g + яблоко 1шт","drink":None,
     "items":["Творог 5% 150g","Яблоко 1шт"],"kcal":260,"protein":26,"carbs":26,"fat":8},
    {"id":"snack2","time":"16:00","emoji":"🥛",
     "display":"Греческий йогурт 150g + орехи грецкие 15g","drink":None,
     "items":["Греческий йогурт 150g","Орехи грецкие 15g"],"kcal":240,"protein":18,"carbs":14,"fat":16},
    {"id":"snack2","time":"16:00","emoji":"🥛",
     "display":"Кефир 1% 250мл + кешью 20g","drink":None,
     "items":["Кефир 1% 250мл","Кешью 20g"],"kcal":250,"protein":14,"carbs":18,"fat":14},
]

DINNERS = [
    {"id":"dinner","time":"19:30","emoji":"🌙",
     "display":"Треска 250g + картофель 150g + брокколи 200g","drink":None,
     "items":["Треска 250g","Картофель 150g","Брокколи 200g"],
     "kcal":430,"protein":50,"carbs":38,"fat":4},
    {"id":"dinner","time":"19:30","emoji":"🌙",
     "display":"Куриная грудка 150g + гречка 80g + огурец + помидор","drink":None,
     "items":["Куриное филе 150g","Гречка 80g","Огурец 1шт","Помидор 1шт"],
     "kcal":430,"protein":42,"carbs":36,"fat":8},
    {"id":"dinner","time":"19:30","emoji":"🌙",
     "display":"Горбуша 200g + рис 80g + брокколи 150g","drink":None,
     "items":["Горбуша 200g","Рис 80g","Брокколи 150g"],
     "kcal":480,"protein":40,"carbs":36,"fat":16},
    {"id":"dinner","time":"19:30","emoji":"🌙",
     "display":"Минтай 300g + картофель 100g + огурец + помидор","drink":None,
     "items":["Минтай 300g","Картофель 100g","Огурец 1шт","Помидор 1шт"],
     "kcal":385,"protein":52,"carbs":30,"fat":4},
    {"id":"dinner","time":"19:30","emoji":"🌙",
     "display":"Индейка 150g + гречка 80g + помидор + перец болгарский","drink":None,
     "items":["Индейка 150g","Гречка 80g","Помидор 1шт","Перец болгарский 1шт"],
     "kcal":415,"protein":44,"carbs":36,"fat":7},
    {"id":"dinner","time":"19:30","emoji":"🌙",
     "display":"Треска 200g + рис 80g + брокколи 150g + морковь 100g","drink":None,
     "items":["Треска 200g","Рис 80g","Брокколи 150g","Морковь 100g"],
     "kcal":400,"protein":42,"carbs":40,"fat":4},
    {"id":"dinner","time":"19:30","emoji":"🌙",
     "display":"Куриная грудка 150g + картофель 100g + брокколи 150g","drink":None,
     "items":["Куриное филе 150g","Картофель 100g","Брокколи 150g","Огурец 1шт"],
     "kcal":420,"protein":44,"carbs":34,"fat":7},
]

plan = []
for i in range(28):
    b  = copy.deepcopy(BREAKFASTS[i % 7])
    s1 = copy.deepcopy(SNACKS1[i % 4])
    l  = copy.deepcopy(LUNCHES[i % 7])
    s2 = copy.deepcopy(SNACKS2[i % 4])
    d  = copy.deepcopy(DINNERS[i % 7])
    plan.append({
        "day": i + 1,
        "total_kcal": b["kcal"]+s1["kcal"]+l["kcal"]+s2["kcal"]+d["kcal"],
        "water_liters": 3.0,
        "macros": {
            "protein": b["protein"]+s1["protein"]+l["protein"]+s2["protein"]+d["protein"],
            "carbs":   b["carbs"]+s1["carbs"]+l["carbs"]+s2["carbs"]+d["carbs"],
            "fat":     b["fat"]+s1["fat"]+l["fat"]+s2["fat"]+d["fat"],
        },
        "note": "",
        "meals": [b, s1, l, s2, d]
    })

out = os.path.join(BASE_DIR, "meal_plan_28.json")
with open(out, "w", encoding="utf-8") as f:
    json.dump(plan, f, ensure_ascii=False, indent=2)

print(f"OK: {len(plan)} days")
for day in plan[:4]:
    print(f"  Day {day['day']:2d}: {day['total_kcal']} kcal  B:{day['macros']['protein']} U:{day['macros']['carbs']} F:{day['macros']['fat']}")
