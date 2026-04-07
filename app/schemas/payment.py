from pydantic import BaseModel
class ConnectAccountRequest(BaseModel):
    mechanic_id: str  


class ConnectAccountResponse(BaseModel):
    stripe_account_id: str
    onboarding_url: str


class AccountStatusResponse(BaseModel):
    stripe_account_id: str
    charges_enabled: bool
    payouts_enabled: bool
    details_submitted: bool