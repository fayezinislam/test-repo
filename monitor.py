import os
import json
import time

duration = 10

while(True):
    result = os.popen("curl -s -w '\\n%{http_code}' -H 'Content-Type: application/json' -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICI3MTEwZTIyMi02ZGM2LTQ4MmYtOGE1OS0wOTcwYmQ2NjdkZGQifQ.eyJleHAiOjE5NzQwNjc1NzA0MDksIm5iZiI6MTY1ODQ0ODM3MDQwOSwiaWF0IjoxNjU4NDQ4MzcwNDA5LCJqdGkiOiIxYWNjOTlhNS0zMjYxLTRmNjAtYjYyZS1jOWNjMDc3OGJjOWUiLCJzdWIiOiIxYWNjOTlhNS0zMjYxLTRmNjAtYjYyZS1jOWNjMDc3OGJjOWUifQ.-kag91ZG52mi5d4IxaSJnykJ5aX-jDmDvMdmFroM0iM' https://api2.hiveos.farm/api/v2/farms/1649638/workers/3441179").read()
    suffix = '\n200'
    data = json.loads(result.removesuffix(suffix))
    print(f"round: 1, name: {data['name']}, online: {data['stats'].get('online')}")

    if not data['stats'].get('online'):
        time.sleep(duration)
        result = os.popen("curl -s -w '\\n%{http_code}' -H 'Content-Type: application/json' -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICI3MTEwZTIyMi02ZGM2LTQ4MmYtOGE1OS0wOTcwYmQ2NjdkZGQifQ.eyJleHAiOjE5NzQwNjc1NzA0MDksIm5iZiI6MTY1ODQ0ODM3MDQwOSwiaWF0IjoxNjU4NDQ4MzcwNDA5LCJqdGkiOiIxYWNjOTlhNS0zMjYxLTRmNjAtYjYyZS1jOWNjMDc3OGJjOWUiLCJzdWIiOiIxYWNjOTlhNS0zMjYxLTRmNjAtYjYyZS1jOWNjMDc3OGJjOWUifQ.-kag91ZG52mi5d4IxaSJnykJ5aX-jDmDvMdmFroM0iM' https://api2.hiveos.farm/api/v2/farms/1649638/workers/3441179").read()
        suffix = '\n200'
        data = json.loads(result.removesuffix(suffix))
        print(f"round: 2, name: {data['name']}, online: {data['stats'].get('online')}")

        if not data['stats'].get('online'):
            print('restarting...')
            os.popen("sreboot wakealarm 30").read()
            exit(0)

    print(f'waiting {duration} seconds')
    time.sleep(duration)
