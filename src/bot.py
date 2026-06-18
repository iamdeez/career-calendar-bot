import os
import discord
from discord import app_commands
from discord.ext import tasks
from datetime import datetime
from dotenv import load_dotenv

from . import calendar_service as cal
from .cert_data import find_cert, get_category_emoji, CATEGORIES

load_dotenv()

GUILD_ID = os.getenv("DISCORD_GUILD_ID")
CALENDAR_ID = os.getenv("CALENDAR_ID", "primary")

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


# ── 이벤트 ─────────────────────────────────────────────────────────────────

@client.event
async def on_ready():
    guild = discord.Object(id=int(GUILD_ID)) if GUILD_ID else None
    if guild:
        tree.copy_global_to(guild=guild)
        await tree.sync(guild=guild)
    else:
        await tree.sync()
    print(f"✅ {client.user} 로그인 완료")
    daily_reminder.start()


# ── 슬래시 커맨드 ──────────────────────────────────────────────────────────

@tree.command(name="일정추가", description="Google Calendar에 일정을 추가합니다")
@app_commands.describe(
    제목="일정 제목",
    날짜="날짜 (예: 2025-08-15 또는 2025-08-15 09:00)",
    카테고리="카테고리 선택",
    메모="추가 설명 (선택)",
)
@app_commands.choices(카테고리=[
    app_commands.Choice(name=k, value=k) for k in CATEGORIES
])
async def add_event_cmd(
    interaction: discord.Interaction,
    제목: str,
    날짜: str,
    카테고리: str = "기타",
    메모: str = "",
):
    await interaction.response.defer(ephemeral=False)
    try:
        emoji = get_category_emoji(카테고리)
        full_title = f"{emoji} [{카테고리}] {제목}"
        event = cal.add_event(full_title, 날짜, 메모, CALENDAR_ID)
        link = event.get("htmlLink", "")
        embed = discord.Embed(
            title="✅ 일정 추가 완료",
            color=discord.Color.green(),
        )
        embed.add_field(name="제목", value=full_title, inline=False)
        embed.add_field(name="날짜", value=날짜, inline=True)
        embed.add_field(name="카테고리", value=f"{emoji} {카테고리}", inline=True)
        if 메모:
            embed.add_field(name="메모", value=메모, inline=False)
        if link:
            embed.add_field(name="캘린더 링크", value=f"[열기]({link})", inline=False)
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"❌ 오류: {e}", ephemeral=True)


@tree.command(name="일정목록", description="이번 달 또는 특정 월의 일정을 조회합니다")
@app_commands.describe(
    년도="년도 (기본: 현재 년도)",
    월="월 (기본: 현재 월)",
)
async def list_events_cmd(
    interaction: discord.Interaction,
    년도: int = 0,
    월: int = 0,
):
    await interaction.response.defer()
    now = datetime.now()
    year = 년도 or now.year
    month = 월 or now.month

    try:
        events = cal.list_events(year, month, CALENDAR_ID)
        if not events:
            await interaction.followup.send(f"📭 {year}년 {month}월에 등록된 일정이 없습니다.")
            return

        embed = discord.Embed(
            title=f"📅 {year}년 {month}월 일정 ({len(events)}개)",
            color=discord.Color.blue(),
        )
        for event in events[:20]:
            date_str = cal.get_event_date(event)
            dday = cal.calc_dday(event)
            dday_str = f"D-{dday}" if dday > 0 else ("D-Day" if dday == 0 else f"D+{abs(dday)}")
            title = event.get("summary", "(제목 없음)")
            embed.add_field(
                name=f"{date_str}  `{dday_str}`",
                value=title,
                inline=False,
            )

        if len(events) > 20:
            embed.set_footer(text=f"외 {len(events) - 20}개 더 있습니다.")
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"❌ 오류: {e}", ephemeral=True)


@tree.command(name="디데이", description="자격증 또는 일정 이름으로 D-day를 조회합니다")
@app_commands.describe(검색어="자격증 이름 또는 일정 제목 일부")
async def dday_cmd(interaction: discord.Interaction, 검색어: str):
    await interaction.response.defer()
    try:
        events = cal.get_upcoming_events(days=365, calendar_id=CALENDAR_ID)
        matched = [e for e in events if 검색어.lower() in e.get("summary", "").lower()]

        if not matched:
            cert_name, cert_info = find_cert(검색어)
            if cert_info:
                embed = discord.Embed(
                    title=f"📜 {cert_name} 정보",
                    color=discord.Color.orange(),
                )
                embed.add_field(name="주관", value=cert_info["org"], inline=True)
                embed.add_field(name="시행", value=cert_info["schedule_note"], inline=True)
                embed.add_field(name="공식 사이트", value=cert_info["url"], inline=False)
                embed.set_footer(text="캘린더에 직접 일정을 추가하려면 /일정추가 를 사용하세요.")
                await interaction.followup.send(embed=embed)
            else:
                await interaction.followup.send(f"🔍 '{검색어}'에 해당하는 일정을 찾지 못했습니다.")
            return

        embed = discord.Embed(
            title=f"🔍 '{검색어}' 검색 결과 ({len(matched)}개)",
            color=discord.Color.purple(),
        )
        for event in matched[:10]:
            dday = cal.calc_dday(event)
            date_str = cal.get_event_date(event)
            if dday > 0:
                dday_str = f"⏳ D-{dday}"
            elif dday == 0:
                dday_str = "🔥 D-Day!"
            else:
                dday_str = f"✅ D+{abs(dday)} (완료)"
            embed.add_field(
                name=event.get("summary", "(제목 없음)"),
                value=f"{date_str}  **{dday_str}**",
                inline=False,
            )
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"❌ 오류: {e}", ephemeral=True)


@tree.command(name="다음일정", description="앞으로 N일 이내의 일정을 조회합니다")
@app_commands.describe(일수="조회할 기간 (기본 7일)")
async def upcoming_cmd(interaction: discord.Interaction, 일수: int = 7):
    await interaction.response.defer()
    try:
        events = cal.get_upcoming_events(days=일수, calendar_id=CALENDAR_ID)
        if not events:
            await interaction.followup.send(f"📭 앞으로 {일수}일 내에 예정된 일정이 없습니다.")
            return

        embed = discord.Embed(
            title=f"⏰ 앞으로 {일수}일 내 일정 ({len(events)}개)",
            color=discord.Color.gold(),
        )
        for event in events[:15]:
            dday = cal.calc_dday(event)
            date_str = cal.get_event_date(event)
            dday_str = f"D-{dday}" if dday > 0 else "D-Day"
            embed.add_field(
                name=event.get("summary", "(제목 없음)"),
                value=f"{date_str}  `{dday_str}`",
                inline=False,
            )
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"❌ 오류: {e}", ephemeral=True)


@tree.command(name="자격증정보", description="IT 자격증 정보를 조회합니다")
@app_commands.describe(자격증명="자격증 이름 (예: 정처기, SQLD, AWS)")
async def cert_info_cmd(interaction: discord.Interaction, 자격증명: str):
    cert_name, cert_info = find_cert(자격증명)
    if not cert_info:
        await interaction.response.send_message(
            f"❌ '{자격증명}'에 대한 정보를 찾지 못했습니다.\n"
            "지원 자격증: 정보처리기사, 정보보안기사, SQLD, SQLP, ADsP, AWS-SAA 등",
            ephemeral=True,
        )
        return

    embed = discord.Embed(
        title=f"📜 {cert_name}",
        color=discord.Color.teal(),
    )
    embed.add_field(name="주관 기관", value=cert_info["org"], inline=False)
    embed.add_field(name="시험 일정", value=cert_info["schedule_note"], inline=False)
    embed.add_field(name="공식 사이트", value=cert_info["url"], inline=False)
    await interaction.response.send_message(embed=embed)


# ── 자동 알림 (매일 오전 9시) ─────────────────────────────────────────────

REMINDER_CHANNEL_ID = int(os.getenv("REMINDER_CHANNEL_ID", "0"))


@tasks.loop(hours=24)
async def daily_reminder():
    if not REMINDER_CHANNEL_ID:
        return
    channel = client.get_channel(REMINDER_CHANNEL_ID)
    if not channel:
        return

    try:
        events = cal.get_upcoming_events(days=7, calendar_id=CALENDAR_ID)
        urgent = [e for e in events if cal.calc_dday(e) <= 3]
        if not urgent:
            return

        embed = discord.Embed(
            title="🔔 D-3 이내 임박 일정 알림",
            color=discord.Color.red(),
        )
        for event in urgent:
            dday = cal.calc_dday(event)
            label = "D-Day!" if dday == 0 else f"D-{dday}"
            embed.add_field(
                name=event.get("summary", "(제목 없음)"),
                value=f"`{label}`  —  {cal.get_event_date(event)}",
                inline=False,
            )
        await channel.send(embed=embed)
    except Exception as e:
        print(f"알림 오류: {e}")


def run():
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise ValueError(".env 파일에 DISCORD_TOKEN이 없습니다.")
    client.run(token)
