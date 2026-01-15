from pydantic import BaseModel, Field


class FoodNutritionItem(BaseModel):
  food_name: str = Field(..., description="标准化的食物名称")
  weight: float = Field(..., ge=0, description="重量，单位为克(g)")
  unit: str = Field(default="g", description="单位，建议为g")
  calories: float = Field(..., ge=0, description="能量，单位为千卡(kcal)")
  carbohydrates: float = Field(..., ge=0, description="碳水化合物，单位为克(g)")
  protein: float = Field(..., ge=0, description="蛋白质，单位为克(g)")
  fat: float = Field(..., ge=0, description="脂肪，单位为克(g)")


class MealTotals(BaseModel):
  weight: float
  calories: float
  carbohydrates: float
  protein: float
  fat: float


class MealAnalyzeMeta(BaseModel):
  filename: str
  size: int
  mime: str
  model: str | None = None
  used_json_schema: bool | None = None


class MealAnalyzeResponse(BaseModel):
  foods: list[FoodNutritionItem]
  totals: MealTotals
  meta: MealAnalyzeMeta

