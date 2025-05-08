from database.models.funnel_user_actions import FunnelUserAction


class FunnelActions:
    @staticmethod
    async def save(user_id: int, action: str, session, details: str | None = None):
        bot_id = session.info.get("bot_id")
        action_obj = FunnelUserAction(bot_id=bot_id, user_id=user_id, action=action, details=details)
        session.add(action_obj)
        await session.commit()