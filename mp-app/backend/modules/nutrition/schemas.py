"""اسکیمای nutrition."""

from __future__ import annotations

from pydantic import BaseModel, Field


class MealItemIn(BaseModel):
    food_id: int
    meal_slot: str = Field(..., pattern="^(breakfast|lunch|dinner|snack)$")
    grams: int = Field(..., gt=0, le=2000)
    order: int = 0


class PlanFromEngineIn(BaseModel):
    member_id: int
    daily_kcal: int = Field(..., gt=500, le=10000)
    protein_g: int = Field(..., ge=0)
    carbs_g: int = Field(..., ge=0)
    fat_g: int = Field(..., ge=0)
    engine_version: str = ""
    llm_explanation: str = Field("", max_length=4000)
    meals: list[MealItemIn] = []


class MealItemOut(BaseModel):
    id: int
    food_id: int
    meal_slot: str
    grams: int
    order: int

    model_config = {"from_attributes": True}


class PlanOut(BaseModel):
    id: int
    member_id: int
    coach_id: int | None
    status: str
    daily_kcal: int
    protein_g: int
    carbs_g: int
    fat_g: int
    engine_version: str
    llm_explanation: str
    meals: list[MealItemOut] = []

    model_config = {"from_attributes": True}
