app_os = globals().get("app_os")  # получаем API от оболочки

print("Простой калькулятор. Введите 'exit' для выхода.")

while True:
    expr = input("Введите выражение: ")
    if expr.strip().lower() == "exit":
        print("Выход из калькулятора.")
        break
    try:
        # вычисляем выражение (осторожно, eval!)
        result = eval(expr, {"__builtins__": {}}, {})
        print("Результат:", result)
    except Exception as e:
        print("Ошибка:", e)
