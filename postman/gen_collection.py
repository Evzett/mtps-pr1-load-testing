"""Генератор Postman-коллекции (формат v2.1) с 18 тест-кейсами для JSONPlaceholder.

Коллекция генерируется скриптом, чтобы тест-кейсы были описаны в одном месте
и их можно было одновременно вывести в таблицу отчёта (test_cases.csv).
Результат: JSONPlaceholder.postman_collection.json — импортируется в Postman
или запускается через Newman (CLI-раннер Postman).
"""
import csv
import json
import pathlib

HERE = pathlib.Path(__file__).parent
BASE = "{{baseUrl}}"

# (ID, название, метод, путь, тело, ожидаемый статус, JS-проверки, ожидаемый результат для отчёта)
CASES = [
    ("TC-01", "Получение списка всех постов", "GET", "/posts", None, 200,
     ["pm.expect(json).to.be.an('array').with.lengthOf(100);",
      "pm.expect(json[0]).to.have.all.keys('userId','id','title','body');"],
     "200, массив из 100 постов с полями userId, id, title, body"),
    ("TC-02", "Получение поста по ID", "GET", "/posts/1", None, 200,
     ["pm.expect(json.id).to.eql(1);", "pm.expect(json.userId).to.eql(1);"],
     "200, объект поста с id = 1"),
    ("TC-03", "Фильтрация постов по пользователю", "GET", "/posts?userId=1", None, 200,
     ["pm.expect(json).to.have.lengthOf(10);",
      "json.forEach(p => pm.expect(p.userId).to.eql(1));"],
     "200, 10 постов, у всех userId = 1"),
    ("TC-04", "Получение несуществующего поста", "GET", "/posts/0", None, 404,
     ["pm.expect(json).to.eql({});"],
     "404, пустой объект"),
    ("TC-05", "Получение комментариев к посту (вложенный ресурс)", "GET", "/posts/1/comments", None, 200,
     ["pm.expect(json).to.have.lengthOf(5);",
      "json.forEach(c => { pm.expect(c.postId).to.eql(1); pm.expect(c.email).to.include('@'); });"],
     "200, 5 комментариев с postId = 1 и корректным email"),
    ("TC-06", "Фильтрация комментариев по посту", "GET", "/comments?postId=1", None, 200,
     ["pm.expect(json).to.have.lengthOf(5);"],
     "200, 5 комментариев (совпадает с TC-05)"),
    ("TC-07", "Получение списка пользователей", "GET", "/users", None, 200,
     ["pm.expect(json).to.have.lengthOf(10);",
      "pm.expect(json[0]).to.include.keys('id','name','username','email','address','company');"],
     "200, 10 пользователей с вложенными address и company"),
    ("TC-08", "Получение пользователя по ID", "GET", "/users/1", None, 200,
     ["pm.expect(json.username).to.eql('Bret');",
      "pm.expect(json.address.geo).to.have.all.keys('lat','lng');"],
     "200, пользователь Bret с координатами address.geo"),
    ("TC-09", "Получение несуществующего пользователя", "GET", "/users/9999", None, 404,
     ["pm.expect(json).to.eql({});"],
     "404, пустой объект"),
    ("TC-10", "Фильтрация задач по статусу", "GET", "/todos?completed=true", None, 200,
     ["pm.expect(json.length).to.be.above(0);",
      "json.forEach(t => pm.expect(t.completed).to.be.true);"],
     "200, непустой массив, все задачи completed = true"),
    ("TC-11", "Получение задачи по ID", "GET", "/todos/1", None, 200,
     ["pm.expect(json).to.have.all.keys('userId','id','title','completed');",
      "pm.expect(json.completed).to.be.a('boolean');"],
     "200, задача с булевым полем completed"),
    ("TC-12", "Получение фотографий альбома (вложенный ресурс)", "GET", "/albums/1/photos", None, 200,
     ["pm.expect(json).to.have.lengthOf(50);",
      "pm.expect(json[0].url).to.match(/^https?:\\/\\//);"],
     "200, 50 фотографий с корректными URL"),
    ("TC-13", "Фильтрация по несуществующему значению", "GET", "/posts?userId=9999", None, 200,
     ["pm.expect(json).to.be.an('array').that.is.empty;"],
     "200, пустой массив"),
    ("TC-14", "Создание поста", "POST", "/posts",
     {"title": "load test", "body": "created by test", "userId": 1}, 201,
     ["pm.expect(json.id).to.eql(101);", "pm.expect(json.title).to.eql('load test');"],
     "201, созданный объект с id = 101"),
    ("TC-15", "Полное обновление поста", "PUT", "/posts/1",
     {"id": 1, "title": "updated", "body": "updated body", "userId": 1}, 200,
     ["pm.expect(json.title).to.eql('updated');", "pm.expect(json.body).to.eql('updated body');"],
     "200, объект с новыми title и body"),
    ("TC-16", "Частичное обновление поста", "PATCH", "/posts/1", {"title": "patched"}, 200,
     ["pm.expect(json.title).to.eql('patched');", "pm.expect(json.body).to.be.a('string').and.not.empty;"],
     "200, изменён только title, body сохранён"),
    ("TC-17", "Удаление поста", "DELETE", "/posts/1", None, 200,
     ["pm.expect(json).to.eql({});"],
     "200, пустой объект"),
    ("TC-18", "Обращение к несуществующему ресурсу", "GET", "/unknown-resource", None, 404,
     [],
     "404"),
]


def make_item(case):
    tc_id, name, method, path, body, status, checks, _ = case
    raw_path, _, query = path.partition("?")
    url = {
        "raw": BASE + path,
        "host": [BASE],
        "path": [p for p in raw_path.split("/") if p],
    }
    if query:
        url["query"] = [dict(zip(("key", "value"), q.split("="))) for q in query.split("&")]
    script = [
        f"pm.test('{tc_id}: статус {status}', () => pm.response.to.have.status({status}));",
        "pm.test('Время ответа < 2000 мс', () => pm.expect(pm.response.responseTime).to.be.below(2000));",
    ]
    if checks:
        script.append("pm.test('Заголовок Content-Type: application/json', () => "
                      "pm.expect(pm.response.headers.get('Content-Type')).to.include('application/json'));")
        script.append("const json = pm.response.json();")
        script.append(f"pm.test('{tc_id}: тело ответа', () => {{ " + " ".join(checks) + " });")
    request = {"method": method, "header": [], "url": url}
    if body is not None:
        request["header"] = [{"key": "Content-Type", "value": "application/json; charset=UTF-8"}]
        request["body"] = {"mode": "raw", "raw": json.dumps(body, ensure_ascii=False),
                           "options": {"raw": {"language": "json"}}}
    return {
        "name": f"{tc_id} {name}",
        "event": [{"listen": "test", "script": {"type": "text/javascript", "exec": script}}],
        "request": request,
    }


def main():
    collection = {
        "info": {
            "name": "JSONPlaceholder — функциональные тест-кейсы",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        },
        "variable": [{"key": "baseUrl", "value": "https://jsonplaceholder.typicode.com"}],
        "item": [make_item(c) for c in CASES],
    }
    (HERE / "JSONPlaceholder.postman_collection.json").write_text(
        json.dumps(collection, ensure_ascii=False, indent=2), encoding="utf-8")
    with open(HERE / "test_cases.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["ID", "Название", "Метод", "Эндпойнт", "Тело запроса", "Ожидаемый результат"])
        for tc_id, name, method, path, body, _status, _checks, expected in CASES:
            w.writerow([tc_id, name, method, path,
                        json.dumps(body, ensure_ascii=False) if body else "—", expected])
    print(f"Сгенерировано тест-кейсов: {len(CASES)}")


if __name__ == "__main__":
    main()
