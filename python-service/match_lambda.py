# match_lambda.py
import json

def lambda_handler(event, context):
    """
    event["orders"] = [ {...}, {...} ]  # CSV/Excel解析済みの発注データ
    event["invoices"] = [ {...}, {...} ] # PDF解析済みの請求データ
    """
    orders = event.get("orders", [])
    invoices = event.get("invoices", [])

    diff_rows = match_csv_and_pdf(orders, invoices)

    return {
        "statusCode": 200,
        "body": json.dumps({"diff_rows": diff_rows})
    }

def match_csv_and_pdf(csv_data, pdf_extracted):
    """
    CSVの各行をループし、PDFの全明細をチェックして:
      - 業者名 / 建物名 / 番号 / 支払金額 の4つが「レーベンシュタイン距離2以内」で一致なら OK
      - 見つからない場合は DIFF

    ※ 上記4つの比較では、文字列内のスペースを削除＆ASCIIを全角に変換してから比較
    """

    expected_headers = [
        "業者ID", "業者名", "コード", "建物名", "番号", "受付内容",
        "支払金額", "修繕作成者", "完工日", "修繕業者ID", "支払サイト",
        "支払日", "立替金", "請求日"
    ]

    # PDFをフラット化 (複数ファイル分を1リストに集約)
    all_pdf_rows = []
    for pdf_list in pdf_extracted:
        all_pdf_rows.extend(pdf_list)

    diff_rows = []

    # CSVを1行ずつループ
    for c_item in csv_data:
        matched_any = False
        matched_pdf = None

        # PDF全明細をチェック
        for p_item in all_pdf_rows:
            # PDF "金額" を文字列化
            pdf_money_val = p_item.get("金額", "")
            if isinstance(pdf_money_val, (int, float)):
                pdf_money_val = str(pdf_money_val)

            # 1) CSVの 業者名/建物名/番号/支払金額 を正規化
            c_name  = remove_spaces_and_to_fullwidth(c_item.get("業者名", ""))
            c_build = remove_spaces_and_to_fullwidth(c_item.get("建物名", ""))
            c_room  = remove_spaces_and_to_fullwidth(c_item.get("番号", ""))
            c_money = remove_spaces_and_to_fullwidth(c_item.get("支払金額", ""))

            # 2) PDF側の 工事業者名/物件名/部屋番号/金額 を正規化
            p_name  = remove_spaces_and_to_fullwidth(p_item.get("工事業者名", ""))
            p_build = remove_spaces_and_to_fullwidth(p_item.get("物件名", ""))
            p_room  = remove_spaces_and_to_fullwidth(p_item.get("部屋番号", ""))
            p_money = remove_spaces_and_to_fullwidth(pdf_money_val)

            # ---------- 2文字まで誤差を許容する一致判定 ----------
            if (
                within_distance(c_name,  p_name)   and
                within_distance(c_build, p_build)  and
                within_distance(c_room,  p_room)   and
                within_distance(c_money, p_money)
            ):
                matched_any = True
                matched_pdf = p_item
                break  # 1行マッチすれば終了
            else:
                # デバッグ用ログ（不要なら削除）
                print("c_item==========================")
                print(c_item)
                print("p_item==========================")
                print(p_item)

        # diff_rowを作成
        diff_row = {}
        for header_name in expected_headers:
            diff_row[f"csv_{header_name}"] = c_item.get(header_name, "")

        if matched_any and matched_pdf:
            # PDF辞書を CSVキーにマッピング
            normalized_pdf = {}

            # 業者IDは "発注番号" を代用する例
            pdf_id = matched_pdf.get("業者ID", "")
            if not pdf_id or pdf_id == "不明":
                pdf_id = matched_pdf.get("発注番号", "")
            normalized_pdf["業者ID"] = pdf_id

            normalized_pdf["業者名"]     = matched_pdf.get("工事業者名", "")
            normalized_pdf["建物名"]     = matched_pdf.get("物件名", "")
            normalized_pdf["番号"]       = matched_pdf.get("部屋番号", "")
            # 金額を文字列化
            money_val = matched_pdf.get("金額", "")
            if isinstance(money_val, (int, float)):
                money_val = str(money_val)
            normalized_pdf["支払金額"] = money_val

            # 残りの項目を適宜セット
            normalized_pdf["コード"]       = matched_pdf.get("コード", "")
            normalized_pdf["受付内容"]     = matched_pdf.get("受付内容", "")
            normalized_pdf["修繕作成者"]  = matched_pdf.get("修繕作成者", "")
            normalized_pdf["完工日"]      = matched_pdf.get("完工日", "")
            normalized_pdf["修繕業者ID"]  = matched_pdf.get("修繕業者ID", "")
            normalized_pdf["支払サイト"]  = matched_pdf.get("支払サイト", "")
            normalized_pdf["支払日"]     = matched_pdf.get("支払日", "")
            normalized_pdf["立替金"]     = matched_pdf.get("立替金", "")
            normalized_pdf["請求日"]     = matched_pdf.get("請求日", "")

            for header_name in expected_headers:
                diff_row[f"pdf_{header_name}"] = normalized_pdf.get(header_name, "")

            diff_row["status"] = "OK"
        else:
            # 見つからなかった → PDFは空、ステータス=DIFF
            for header_name in expected_headers:
                diff_row[f"pdf_{header_name}"] = ""
            diff_row["status"] = "DIFF"

        diff_rows.append(diff_row)

    return diff_rows

def remove_spaces_and_to_fullwidth(s: str) -> str:
    """
    文字列 s から半角スペース(\u0020)と全角スペース(\u3000)を削除し、
    ASCII 英数字や記号は全角（0xFF01-0xFF5Eの範囲）に変換する。
    """
    if not s:
        return ""

    # 1) 半角/全角スペース削除
    #   " " (U+0020) / "　" (U+3000)
    s = s.replace(" ", "").replace("\u3000", "")

    # 2) ASCII文字(0x21～0x7E)を全角(0xFF01～0xFF5E)に変換
    result = []
    for ch in s:
        code = ord(ch)
        if 0x21 <= code <= 0x7E:
            result.append(chr(code + 0xFEE0))
        else:
            result.append(ch)
    return "".join(result)

def within_distance(str_a, str_b, max_dist=2):
    """
    レーベンシュタイン距離が max_dist 以下なら True
    """
    return levenshtein_distance(str_a, str_b) <= max_dist

# --- 突合ロジック ---
def levenshtein_distance(a, b):
    """
    文字列 a と b のレーベンシュタイン距離を求める関数
        - 文字の挿入/削除/置換コストを1として計算
    """
    if a == b:
        return 0
    len_a, len_b = len(a), len(b)
    if len_a == 0:
        return len_b
    if len_b == 0:
        return len_a

    # 動的計画法 (DP) で距離計算
    dp = [[0]*(len_b+1) for _ in range(len_a+1)]
    for i in range(len_a+1):
        dp[i][0] = i
    for j in range(len_b+1):
        dp[0][j] = j

    for i in range(1, len_a+1):
        for j in range(1, len_b+1):
            cost = 0 if a[i-1] == b[j-1] else 1
            dp[i][j] = min(
                dp[i-1][j] + 1,    # 削除
                dp[i][j-1] + 1,    # 挿入
                dp[i-1][j-1] + cost  # 置換
            )

    return dp[len_a][len_b]

