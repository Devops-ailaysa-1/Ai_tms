
from google.genai import types
from google import genai

pib_trans_result_schema = genai.types.Schema(
            type=genai.types.Type.OBJECT,
            required=["translated_result"],
            properties={
                "translated_result": genai.types.Schema(
                    type=genai.types.Type.STRING
                )
            },
        )




pib_transcription_result =  response_schema=genai.types.Schema(
            type = genai.types.Type.OBJECT,
            required = ["result"],
            properties = {
                "result": genai.types.Schema(
                    type = genai.types.Type.ARRAY,
                    items = genai.types.Schema(
                        type = genai.types.Type.OBJECT,
                        required = ["timestamp", "transcription_result"],
                        properties = {
                            "timestamp": genai.types.Schema(
                                type = genai.types.Type.STRING,
                            ),
                            "transcription_result": genai.types.Schema(
                                type = genai.types.Type.STRING,
                            ),
                        },
                    ),
                ),
            },
        )