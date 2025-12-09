a = """
    asfasdfasdfasdf<br><br>adasdfasdfasdfasdfasdfa<br><br><br><br><br><br>asdfasdfasdfasdfasdfasfd
"""

res = a.split("<br><br>")
for i in res:
    if i.strip():
        print(i)

