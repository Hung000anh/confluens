from pydantic import BaseModel, Field
from typing import Optional, List


class SymbolBase(BaseModel):
    symbol: str = Field(..., min_length=1, description="Trading symbol")
    exchange: str = Field(default="", description="Exchange name")
    type: str = Field(..., min_length=1, description="Asset type")
    country: str = Field(default="", description="Country")
    base_country: str = Field(default="", description="Base country for pairs")
    quote_country: str = Field(default="", description="Quote country for pairs")


class SymbolCreate(SymbolBase):
    pass


class SymbolUpdate(BaseModel):
    symbol: Optional[str] = None
    exchange: Optional[str] = None
    type: Optional[str] = None
    country: Optional[str] = None
    base_country: Optional[str] = None
    quote_country: Optional[str] = None


class SymbolResponse(SymbolBase):
    id: int
    created_at: str

    class Config:
        from_attributes = True


class IndicatorBase(BaseModel):
    name: str = Field(..., min_length=1, description="Indicator name")
    type: str = Field(..., description="Indicator type (ema, sma)")
    timeframe: str = Field(..., description="Timeframe(s) comma-separated")
    period: int = Field(..., gt=0, description="Period for calculation")
    color: str = Field(default="#10b981", pattern="^#[0-9a-fA-F]{6}$", description="Hex color")


class IndicatorCreate(IndicatorBase):
    pass


class IndicatorUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    timeframe: Optional[str] = None
    period: Optional[int] = None
    color: Optional[str] = None


class IndicatorResponse(IndicatorBase):
    id: int
    is_active: int
    created_at: str

    class Config:
        from_attributes = True


class SettingBase(BaseModel):
    key: str = Field(..., min_length=1, description="Setting key")
    value: str = Field(..., description="Setting value")


class VerifySymbolRequest(BaseModel):
    symbols: List[str]
    exchange: str = ""
