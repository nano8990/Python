# cx_Oracle 패키지 모듈들을 import
import cx_Oracle as oci

# Oracle 서버와 연결(Connection 맺기)
conn = oci.connect('SYSTEM/manager@localhost:1522/xe')

# Connection 확인
print(conn.version)

# Oracle DB의 test_member 테이블 검색(select)
cursor = conn.cursor() # cursor 객체 얻어오기


def moneyTransferSearch(sender, senderUserkey, receiver, receiverUserkey, amount, uuid): #이름 키 이름 키 금액 uuid
    try:
        cursor.execute("SELECT balance FROM BPS_USERS where username = '{}' and userkey = '{}'".format(sender, senderUserkey))  # 송신자, 송신자의 유져 키를 받아서 이걸로 잔고조회를 한다.
        userrow = cursor.fetchall()
    except:
        print("송신자 정보 입력 오류")

    try:
        cursor.execute("SELECT txValidity FROM BPS_TXDATA where uuid = '{}'".format(uuid))  # 개별 트랜잭션번호로 트랜잭션 유효성을 조회
        txrow = cursor.fetchall()
    except:
        print("트랜잭션 정보 조회 오류")

    moneyTransferCommit(sender, senderUserkey, receiver, receiverUserkey, amount, uuid, userrow, txrow)

def moneyTransferCommit(sender, senderUserkey, receiver, receiverUserkey, amount, uuid, userrow, txrow):
    if userrow[0][0] >= amount and txrow[0][0] == None: # 보내려는 금액보다 잔고가 크고 개별 트랙잭션 유효성이 null 값일 때 아래 구문 실행.
        cursor.execute("UPDATE BPS_USERS SET BALANCE = BALANCE-{} WHERE USERNAME = '{}' and userkey = '{}'".format(amount, sender, senderUserkey)) # 송신자 계좌에서 빼준다.
        cursor.execute("UPDATE BPS_USERS SET BALANCE = BALANCE+{} WHERE USERNAME = '{}' and userkey = '{}'".format(amount, receiver, receiverUserkey)) # 수신자 계좌에서 더해준다.
        cursor.execute("UPDATE BPS_TxData SET txValidity = 1 WHERE uuid = '{}'".format(uuid)) # 기본은 null, 1은 유효한 거래
    elif userrow[0][0] < amount:
        cursor.execute("UPDATE BPS_TxData SET txValidity = 0 WHERE uuid = '{}'".format(uuid)) # 기본은 null, 0은 유효하지 않은 거래
    conn.commit()

moneyTransferSearch('AA', 'aa', 'BB', 'bb', 500, 123456789)


conn.commit()

cursor.close() # cursor 객체 닫기

# Oracle 서버와 연결 끊기
conn.close()