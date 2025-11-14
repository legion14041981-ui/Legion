# -*- coding: utf-8 -*-
"""
Legion Specialized Agents Example

Демонстрация работы со специализированными агентами:
- EmailAgent: отправка email через SMTP
- GoogleSheetsAgent: работа с Google Таблицами
- Интеграция агентов для комплексных задач
"""

import asyncio
import os
from pathlib import Path

# Добавляем путь к модулю legion
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from legion import LegionCore
from legion.agents import EmailAgent, GoogleSheetsAgent


async def demo_email_agent():
    """
    Демонстрация работы с EmailAgent
    
    Требуется настройка SMTP в .env:
    EMAIL_SMTP_HOST=smtp.gmail.com
    EMAIL_SMTP_PORT=587
    EMAIL_SMTP_USER=your@gmail.com
    EMAIL_SMTP_PASSWORD=your_password
    EMAIL_FROM=your@gmail.com
    """
    print("\n" + "="*60)
    print("DEMO: EmailAgent - Отправка электронных писем")
    print("="*60 + "\n")
    
    # Создаем EmailAgent
    email_agent = EmailAgent(
        agent_id="email_agent_1",
        name="Email Sender",
        description="Агент для отправки email",
        smtp_host=os.getenv('EMAIL_SMTP_HOST', 'smtp.gmail.com'),
        smtp_port=int(os.getenv('EMAIL_SMTP_PORT', '587')),
        smtp_user=os.getenv('EMAIL_SMTP_USER'),
        smtp_password=os.getenv('EMAIL_SMTP_PASSWORD'),
        from_email=os.getenv('EMAIL_FROM')
    )
    
    # Пример 1: Отправка простого письма
    print("1. Отправка простого письма...")
    result = await email_agent.execute({
        'capability': 'email_send',
        'to': 'recipient@example.com',
        'subject': 'Тестовое письмо из Legion',
        'body': 'Это тестовое письмо, отправленное через EmailAgent.'
    })
    print(f"   Результат: {result}")
    
    # Пример 2: Отправка HTML письма
    print("\n2. Отправка HTML письма...")
    html_body = """
    <html>
        <body>
            <h1>Привет из Legion!</h1>
            <p>Это <strong>HTML</strong> письмо с форматированием.</p>
            <ul>
                <li>Пункт 1</li>
                <li>Пункт 2</li>
                <li>Пункт 3</li>
            </ul>
        </body>
    </html>
    """
    result = await email_agent.execute({
        'capability': 'email_send',
        'to': 'recipient@example.com',
        'subject': 'HTML письмо из Legion',
        'body': html_body,
        'html': True
    })
    print(f"   Результат: {result}")
    
    # Пример 3: Массовая рассылка
    print("\n3. Массовая рассылка...")
    recipients = [
        {'email': 'user1@example.com', 'name': 'User 1'},
        {'email': 'user2@example.com', 'name': 'User 2'},
        {'email': 'user3@example.com', 'name': 'User 3'},
    ]
    
    result = await email_agent.execute({
        'capability': 'email_bulk',
        'recipients': recipients,
        'subject': 'Массовая рассылка из Legion',
        'body': 'Это массовая рассылка для {name}',
        'rate_limit': 2  # 2 письма в секунду
    })
    print(f"   Результат: {result}")
    
    # Статистика
    print(f"\n📊 Статистика EmailAgent:")
    print(f"   Отправлено: {email_agent.emails_sent}")
    print(f"   Ошибок: {email_agent.emails_failed}")
    print(f"   Успешность: {email_agent.success_rate:.1%}")


async def demo_sheets_agent():
    """
    Демонстрация работы с GoogleSheetsAgent
    
    Требуется настройка Google Sheets API:
    GOOGLE_SHEETS_CREDENTIALS=/path/to/credentials.json
    """
    print("\n" + "="*60)
    print("DEMO: GoogleSheetsAgent - Работа с Google Таблицами")
    print("="*60 + "\n")
    
    credentials_path = os.getenv('GOOGLE_SHEETS_CREDENTIALS')
    if not credentials_path:
        print("⚠️  GOOGLE_SHEETS_CREDENTIALS не настроен в .env")
        return
    
    # Создаем GoogleSheetsAgent
    sheets_agent = GoogleSheetsAgent(
        agent_id="sheets_agent_1",
        name="Sheets Manager",
        description="Агент для работы с Google Sheets",
        credentials_path=credentials_path
    )
    
    # ID вашей таблицы (из URL: https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit)
    spreadsheet_id = os.getenv('GOOGLE_SHEETS_ID', 'your_spreadsheet_id_here')
    
    # Пример 1: Чтение данных
    print("1. Чтение данных из таблицы...")
    result = await sheets_agent.execute({
        'capability': 'sheets_read',
        'spreadsheet_id': spreadsheet_id,
        'range': 'Sheet1!A1:C10'
    })
    print(f"   Прочитано строк: {len(result.get('values', []))}")
    
    # Пример 2: Запись данных
    print("\n2. Запись данных в таблицу...")
    data = [
        ['Имя', 'Email', 'Статус'],
        ['Иван', 'ivan@example.com', 'Активен'],
        ['Мария', 'maria@example.com', 'Активна'],
        ['Петр', 'petr@example.com', 'Неактивен'],
    ]
    
    result = await sheets_agent.execute({
        'capability': 'sheets_write',
        'spreadsheet_id': spreadsheet_id,
        'range': 'Sheet1!A1:C4',
        'values': data
    })
    print(f"   Результат: {result}")
    
    # Пример 3: Добавление строк
    print("\n3. Добавление новых строк...")
    new_rows = [
        ['Анна', 'anna@example.com', 'Активна'],
        ['Сергей', 'sergey@example.com', 'Активен'],
    ]
    
    result = await sheets_agent.execute({
        'capability': 'sheets_append',
        'spreadsheet_id': spreadsheet_id,
        'range': 'Sheet1!A:C',
        'values': new_rows
    })
    print(f"   Результат: {result}")
    
    # Статистика
    print(f"\n📊 Статистика GoogleSheetsAgent:")
    print(f"   Операций чтения: {sheets_agent.reads}")
    print(f"   Операций записи: {sheets_agent.writes}")
    print(f"   Обновлений: {sheets_agent.updates}")


async def demo_integration():
    """
    Пример интеграции агентов:
    1. Читаем список email из Google Sheets
    2. Отправляем письма через EmailAgent
    3. Записываем результаты обратно в таблицу
    """
    print("\n" + "="*60)
    print("DEMO: Интеграция агентов")
    print("="*60 + "\n")
    
    # Инициализируем LegionCore
    core = LegionCore()
    
    # Создаем агентов
    email_agent = EmailAgent(
        agent_id="email_agent",
        name="Email Sender",
        smtp_host=os.getenv('EMAIL_SMTP_HOST'),
        smtp_port=int(os.getenv('EMAIL_SMTP_PORT', '587')),
        smtp_user=os.getenv('EMAIL_SMTP_USER'),
        smtp_password=os.getenv('EMAIL_SMTP_PASSWORD'),
        from_email=os.getenv('EMAIL_FROM')
    )
    
    credentials_path = os.getenv('GOOGLE_SHEETS_CREDENTIALS')
    if credentials_path:
        sheets_agent = GoogleSheetsAgent(
            agent_id="sheets_agent",
            name="Sheets Manager",
            credentials_path=credentials_path
        )
    else:
        print("⚠️  Пропускаем интеграцию - GOOGLE_SHEETS_CREDENTIALS не настроен")
        return
    
    # Регистрируем агентов
    await core.register_agent(email_agent)
    await core.register_agent(sheets_agent)
    
    spreadsheet_id = os.getenv('GOOGLE_SHEETS_ID')
    if not spreadsheet_id:
        print("⚠️  GOOGLE_SHEETS_ID не настроен")
        return
    
    # Шаг 1: Читаем данные из таблицы
    print("Шаг 1: Читаем список получателей из Google Sheets...")
    read_result = await sheets_agent.execute({
        'capability': 'sheets_read',
        'spreadsheet_id': spreadsheet_id,
        'range': 'Sheet1!A2:B10'  # Пропускаем заголовок
    })
    
    recipients = read_result.get('values', [])
    print(f"   Найдено получателей: {len(recipients)}")
    
    # Шаг 2: Отправляем письма
    print("\nШаг 2: Отправляем письма...")
    results = []
    for row in recipients:
        if len(row) >= 2:
            name, email = row[0], row[1]
            print(f"   Отправка письма для {name} ({email})...")
            
            result = await email_agent.execute({
                'capability': 'email_send',
                'to': email,
                'subject': 'Персонализированное письмо',
                'body': f'Здравствуйте, {name}!\n\nЭто автоматически сгенерированное письмо.'
            })
            
            status = 'Отправлено' if result.get('success') else 'Ошибка'
            results.append([name, email, status])
    
    # Шаг 3: Записываем результаты обратно
    print("\nШаг 3: Записываем результаты в таблицу...")
    await sheets_agent.execute({
        'capability': 'sheets_write',
        'spreadsheet_id': spreadsheet_id,
        'range': 'Results!A1:C' + str(len(results) + 1),
        'values': [['Имя', 'Email', 'Статус отправки']] + results
    })
    
    print("\n✅ Интеграция завершена успешно!")
    print(f"   Писем отправлено: {email_agent.emails_sent}")
    print(f"   Ошибок: {email_agent.emails_failed}")


async def main():
    """Главная функция с демонстрацией всех примеров"""
    
    print("\n🤖 Legion - Демонстрация специализированных агентов")
    print("=" * 70)
    
    # Проверяем .env
    env_file = Path(__file__).parent.parent / '.env'
    if not env_file.exists():
        print("\n⚠️  ВНИМАНИЕ: Файл .env не найден!")
        print("\nДля работы примеров создайте файл .env с настройками:")
        print("\n# Email")
        print("EMAIL_SMTP_HOST=smtp.gmail.com")
        print("EMAIL_SMTP_PORT=587")
        print("EMAIL_SMTP_USER=your@gmail.com")
        print("EMAIL_SMTP_PASSWORD=your_password")
        print("EMAIL_FROM=your@gmail.com")
        print("\n# Google Sheets")
        print("GOOGLE_SHEETS_CREDENTIALS=/path/to/credentials.json")
        print("GOOGLE_SHEETS_ID=your_spreadsheet_id")
        print("\n" + "="*70)
        return
    
    try:
        # Запускаем демонстрации
        await demo_email_agent()
        await demo_sheets_agent()
        await demo_integration()
        
    except KeyboardInterrupt:
        print("\n\n⏸️  Демонстрация прервана пользователем")
    except Exception as e:
        print(f"\n\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
