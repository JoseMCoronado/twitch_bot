import sqlite3

conn = sqlite3.connect("bot.db")
conn.row_factory = sqlite3.Row

c = conn.cursor()


class Counter:
    def __init__(self, name, game, count, count_type):
        c = conn.cursor()
        c.execute(
            """CREATE TABLE IF NOT EXISTS counter (
                    name text,
                    game text,
                    count integer,
                    count_type text
                    )"""
        )
        conn.commit()
        self.name = name
        self.game = game
        self.count = count
        self.count_type = count_type

    def prepare_search_query(search_vals):
        search_query = second = ""
        for item in list(search_vals.items()):
            key = item[0]
            value = item[1]
            search_query += "%s%s = '%s'" % (second, key, value)
            second = "AND "
        return search_query

    def prepare_create_value_query(vals_list):
        value_count = len(vals_list)
        selected_value = 0
        values = ""
        for val in vals_list:
            selected_value += 1
            values += "'%s'" % (val)
            if selected_value < value_count:
                values += ", "
        return values

    def prepare_update_value_query(update_values):
        value_count = len(update_values)
        update_query = ""
        selected_value = 0
        for val in update_values:
            selected_value += 1
            update_query += "%s='%s'" % (val[0], val[1])
            if selected_value < value_count:
                update_query += ", "
        return update_query

    def create(vals):
        keys = " ,".join(vals.keys())
        vals_list = list(vals.values())
        values = Counter.prepare_create_value_query(vals_list)
        execute_string = "INSERT INTO counter (%s) VALUES (%s)" % (keys, values)
        with conn:
            c.execute(execute_string)

    def write(search_vals, vals):
        update_values = vals.items()
        update_query = Counter.prepare_update_value_query(update_values)
        search_query = Counter.prepare_search_query(search_vals)
        execute_string = "UPDATE counter SET %s WHERE %s" % (update_query, search_query)
        with conn:
            c.execute(execute_string)

    def get(search_vals, all=False):
        search_query = Counter.prepare_search_query(search_vals)
        c.execute("SELECT * FROM counter WHERE %s" % search_query)
        if all:
            record = c.fetchall()
            if record:
                record = [dict(l) for l in record]
        else:
            record = c.fetchone()
            record = dict(record) if record else None

        return record

    def __repr__(self):
        return "counter('{}', '{}', {})".format(
            self.name, self.game, self.count, self.count_type
        )