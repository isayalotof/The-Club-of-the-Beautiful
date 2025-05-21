from pydantic import BaseModel
from typing import Dict, Optional, Any, List

class ScheduleSettings(BaseModel):
    monday: Optional[str] = "9:00 - 20:00"
    tuesday: Optional[str] = "9:00 - 20:00"
    wednesday: Optional[str] = "9:00 - 20:00"
    thursday: Optional[str] = "9:00 - 20:00"
    friday: Optional[str] = "9:00 - 20:00"
    saturday: Optional[str] = "10:00 - 18:00"
    sunday: Optional[str] = "выходной"

class SocialSettings(BaseModel):
    facebook: Optional[str] = None
    instagram: Optional[str] = None
    vk: Optional[str] = None
    telegram: Optional[str] = None

class SeoSettings(BaseModel):
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    meta_keywords: Optional[str] = None

class GeneralSettings(BaseModel):
    salon_name: str = "Салон красоты"
    salon_description: Optional[str] = None
    salon_address: Optional[str] = None
    salon_phone: Optional[str] = None
    salon_email: Optional[str] = None

class SalonSettingsSchema(BaseModel):
    general: GeneralSettings = GeneralSettings()
    schedule: ScheduleSettings = ScheduleSettings()
    social: SocialSettings = SocialSettings()
    seo: SeoSettings = SeoSettings()
    logo_url: Optional[str] = None

    model_config = {"from_attributes": True}

class SettingUpdate(BaseModel):
    key: str
    value: Dict[str, Any]

class SettingResponse(BaseModel):
    key: str
    value: Dict[str, Any] 