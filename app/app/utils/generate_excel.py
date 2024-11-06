import uuid
from io import BytesIO

import pandas as pd
from fastapi.encoders import jsonable_encoder
from fastapi.responses import StreamingResponse
from pandas import ExcelWriter
from pathlib import Path


def generate_excel_file(
    data: dict,
    path: str = str(Path.home() / "Downloads") + "/",
    title: str = "Report",
) -> tuple[str, str]:
    file_name = "{}-{}.xlsx".format(title, str(uuid.uuid4()))
    file_path = path + file_name
    df = pd.DataFrame(data)
    writer = ExcelWriter(file_path)
    df.to_excel(
        excel_writer=writer, sheet_name=title, index=False, engine="openpyxl"
    )
    writer.close()
    return file_path, file_name


def generate_excel_stream(data: dict, title: str = "Report") -> BytesIO:
    output = BytesIO()
    df = pd.DataFrame(data)

    with pd.ExcelWriter(output) as writer:
        df.style.set_properties(**{"text-align": "center"}).to_excel(
            excel_writer=writer,
            sheet_name=title,
            index=False,
        )
        worksheet = writer.sheets[title]

        for i, column in enumerate(df.columns):
            column_len = max(
                df[column].astype(str).apply(len).max(), len(column)
            )
            worksheet.set_column(i, i, column_len + 2)

    output.seek(0)
    return output


def get_excel_file_response(
    data: list, title: str = "Report", exclude: list[str] | None = None
) -> StreamingResponse:
    report_stream = generate_excel_stream(
        jsonable_encoder(data, exclude=exclude),
        title=title,
    )
    headers = {
        "Content-Disposition": f"attachment; filename={title}.xlsx; filename*=UTF-8''{title}.xlsx",
        "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;",
    }

    return StreamingResponse(report_stream, headers=headers)


if __name__ == "__main__":
    test_data = [{"a": 1, "b": 2}, {"a": 6, "b": 5}]
    print("./", generate_excel_file(test_data))
