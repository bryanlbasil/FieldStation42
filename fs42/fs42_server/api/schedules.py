from fastapi import APIRouter
from datetime import datetime
from fs42.station_manager import StationManager
from fs42.liquid_api import LiquidAPI

router = APIRouter(prefix="/schedules", tags=["schedules"])


def _as_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _get_value(obj, key, default=None):
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _content_tags(content):
    tags = set()

    for item in _as_list(content):
        tag = _get_value(item, "tag")
        if tag:
            tags.add(str(tag).lower())

    return tags


def _station_movie_tags(station_config, content_station=None):
    server_conf = StationManager().server_conf
    guide_metadata = server_conf.get("guide_metadata", {})
    movie_tags = guide_metadata.get("movie_tags", {})

    station_names = set()
    if station_config:
        station_names.add(str(station_config.get("network_name", "")).upper())
    if content_station:
        station_names.add(str(content_station).upper())

    tags = set(str(t).lower() for t in movie_tags.get("*", []))

    for station_name in station_names:
        tags.update(str(t).lower() for t in movie_tags.get(station_name, []))

    return tags


def _mark_movie_blocks(station_config, schedule_blocks):
    for block in schedule_blocks or []:
        content = _get_value(block, "content")
        tags = _content_tags(content)

        content_station = None
        content_items = _as_list(content)
        if content_items:
            content_station = _get_value(content_items[0], "station")

        movie_tags = _station_movie_tags(station_config, content_station)
        is_movie = bool(tags.intersection(movie_tags))

        if isinstance(block, dict):
            block["is_movie"] = is_movie
        else:
            setattr(block, "is_movie", is_movie)

    return schedule_blocks


@router.get("/search_all")
async def search_all_schedules(query: str = None):
    if not query:
        station_manager = StationManager()
        all_results = []

        for station in station_manager.stations:
            if station.get("_has_schedule", False):
                try:
                    schedule_blocks = LiquidAPI.get_blocks(station)
                    schedule_blocks = _mark_movie_blocks(station, schedule_blocks)
                    if schedule_blocks:
                        all_results.append({
                            "network_name": station["network_name"],
                            "schedule_blocks": schedule_blocks
                        })
                except Exception as e:
                    all_results.append({
                        "network_name": station["network_name"],
                        "error": str(e),
                        "schedule_blocks": []
                    })

        return {"query": query, "results": all_results}
    else:
        try:
            search_results = LiquidAPI.search_all_blocks(query)
            station_manager = StationManager()
            all_results = []

            for station_name, blocks in search_results.items():
                if blocks:
                    station = station_manager.station_by_name(station_name)
                    blocks = _mark_movie_blocks(station, blocks)
                    all_results.append({
                        "network_name": station_name,
                        "schedule_blocks": blocks
                    })

            return {"query": query, "results": all_results}
        except Exception as e:
            return {"query": query, "error": str(e), "results": []}


@router.get("/search/{network_name}")
async def search_schedule(network_name: str, query: str = None):
    conf = StationManager().station_by_name(network_name)
    if query:
        schedule_blocks = LiquidAPI.search_blocks(conf, query)
    else:
        schedule_blocks = LiquidAPI.get_blocks(conf)

    schedule_blocks = _mark_movie_blocks(conf, schedule_blocks)
    return {"network_name": network_name, "query": query, "schedule_blocks": schedule_blocks}


@router.get("/{network_name}")
async def get_schedule(network_name: str, start: str = None, end: str = None):
    conf = StationManager().station_by_name(network_name)
    sdt = None
    edt = None
    if start and end:
        try:
            sdt = datetime.fromisoformat(start)
            edt = datetime.fromisoformat(end)
        except ValueError:
            return {"error": "Invalid date format. Use ISO format (YYYY-MM-DDTHH:MM:SS) for start and end."}

    schedule_blocks = LiquidAPI.get_blocks(conf, sdt, edt)
    schedule_blocks = _mark_movie_blocks(conf, schedule_blocks)
    return {"network_name": network_name, "schedule_blocks": schedule_blocks}
