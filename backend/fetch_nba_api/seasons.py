# update to 2024 when 2024-25 season is over
def get_total_seasons(start_year=1980, end_year=2023):
    return [f"{year}-{str(year+1)[-2:]}" for year in range(start_year, end_year + 1)]


seasons = get_total_seasons()
print(seasons)
