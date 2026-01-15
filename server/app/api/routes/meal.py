from fastapi import APIRouter, UploadFile, File, HTTPException
from starlette.concurrency import run_in_threadpool

from server.app.schemas.meal import FoodNutritionItem, MealAnalyzeMeta, MealAnalyzeResponse, MealTotals
from server.app.services import meal_service

router = APIRouter(prefix="/meal", tags=["meal"])


@router.post("/analyze", response_model=MealAnalyzeResponse)
async def analyze_meal(file: UploadFile = File(...)) -> MealAnalyzeResponse:
  filename = file.filename or "unnamed"
  try:
    image_bytes, mime_type, size = await meal_service.read_image_upload(file)
  except ValueError as e:
    print(f"[meal_analyze][reject] filename={filename} err={e}")
    raise HTTPException(status_code=400, detail=str(e))
  finally:
    await file.close()

  try:
    result, used_json_schema, model = await run_in_threadpool(
      meal_service.analyze_meal_image_bytes,
      image_bytes,
      mime_type,
    )
  except ValueError as e:
    print(f"[meal_analyze][error] filename={filename} size={size} mime={mime_type} err={e}")
    raise HTTPException(status_code=502, detail=str(e))

  try:
    foods_raw = (result or {}).get("foods") or []
    foods = [FoodNutritionItem(**item) for item in foods_raw]
  except Exception as e:  # noqa: BLE001
    print(f"[meal_analyze][invalid_output] filename={filename} err={e} raw={result}")
    raise HTTPException(status_code=502, detail=f"Invalid model output: {e}")

  totals = MealTotals(
    weight=sum(item.weight for item in foods),
    calories=sum(item.calories for item in foods),
    carbohydrates=sum(item.carbohydrates for item in foods),
    protein=sum(item.protein for item in foods),
    fat=sum(item.fat for item in foods),
  )
  meta = MealAnalyzeMeta(
    filename=filename,
    size=size,
    mime=mime_type,
    model=model,
    used_json_schema=used_json_schema,
  )
  print(
    f"[meal_analyze] filename={filename} size={size} mime={mime_type} foods={len(foods)} model={model} schema={used_json_schema}"
  )
  return MealAnalyzeResponse(foods=foods, totals=totals, meta=meta)

