import cdsapi
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
from matplotlib.colors import ListedColormap, BoundaryNorm
import datetime

def download_era5_data(date, time, area):
    """
    Download ERA5 data for a given date, time, and area.

    Args:
        date (datetime.date): The date for which to download data.
        time (datetime.time): The time for which to download data.
        area (list): The geographical area in the format [North, West, South, East].

    Returns:
        xr.Dataset: The downloaded ERA5 dataset.
    """
    # Set minutes to 00
    time = datetime.time(time.hour, 0)

    client = cdsapi.Client()
    dataset = 'reanalysis-era5-pressure-levels'
    request = {
        'product_type': ['reanalysis'],
        'variable': ['u_component_of_wind', 'v_component_of_wind', 'geopotential'],
        'year': [date.strftime('%Y')],
        'month': [date.strftime('%m')],
        'day': [date.strftime('%d')],
        'time': [time.strftime('%H:%M')],
        'pressure_level': ['500', '300'],  # Two pressure levels for vertical shear
        'format': 'nc',
        'area': area,
    }
    target = 'download.nc'
    client.retrieve(dataset, request, target)
    return xr.open_dataset(target)

def calculate_wind_shear(data):
    """
    Calculate vertical wind shear from the given dataset.

    Args:
        data (xr.Dataset): The dataset containing wind and geopotential data.

    Returns:
        xr.DataArray: The calculated vertical wind shear.
    """
    # U-component of wind (u): East-west wind velocity.
    # V-component of wind (v): North-south wind velocity.
    # Geopotential for height-based calculations.
    u2 = data['u'].sel(pressure_level=300)
    v2 = data['v'].sel(pressure_level=300)
    z2 = data['z'].sel(pressure_level=300)

    u1 = data['u'].sel(pressure_level=500)
    v1 = data['v'].sel(pressure_level=500)
    z1 = data['z'].sel(pressure_level=500)

    delta_u = u1 - u2
    delta_v = v1 - v2
    delta_z = z1 - z2

    vertical_shear = np.sqrt((delta_u / delta_z)**2 + (delta_v / delta_z)**2)
    vertical_shear_squeezed = vertical_shear.isel(valid_time=0).squeeze()

    return vertical_shear_squeezed

def convert_api_to_plot_format(api_coords):
    """
    Convert bounding box coordinates from API format to plot format.

    API format: [North, West, South, East]
    Plot format: [West, East, South, North]

    Args:
        api_coords (list): List of coordinates in API format [North, West, South, East].

    Returns:
        list: List of coordinates in plot format [West, East, South, North].
    """
    north, west, south, east = api_coords
    return [west, east, south, north]

def plot_wind_shear(data, title, filename, continent = [71.0, -31.0, 36.0, 40.0]):
    """
    Plot wind shear data on a map.

    Args:
        data (xr.DataArray): The wind shear data to plot.
        title (str): The title of the plot.
        filename (str): The name of the file to save the plot.
        continent (list, optional): The geographical area in plot format [West, East, South, North]. Defaults to Europe.
    """
    fig, ax = plt.subplots(figsize=(10, 6), subplot_kw={'projection': ccrs.PlateCarree()})
    ax.set_extent(convert_api_to_plot_format(continent), crs=ccrs.PlateCarree())  # Europe

    lat = data['latitude'].values
    lon = data['longitude'].values

    c = ax.pcolormesh(lon, lat, data, cmap='viridis', shading='auto')

    ax.coastlines(resolution='10m')
    ax.gridlines(draw_labels=True)

    ax.set_title(title)
    plt.colorbar(c, ax=ax, orientation='vertical', label='Wind Shear (m/s)')

    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.show()

def calculate_horizontal_shear(data):
    """
    Calculate horizontal wind shear from the given dataset.

    Args:
        data (xr.Dataset): The dataset containing wind data.

    Returns:
        xr.DataArray: The calculated horizontal wind shear.
    """
    u_wind = data['u'].sel(pressure_level=500)
    v_wind = data['v'].sel(pressure_level=500)

    u_lat_gradient = u_wind.differentiate('latitude')
    u_lon_gradient = u_wind.differentiate('longitude')
    v_lat_gradient = v_wind.differentiate('latitude')
    v_lon_gradient = v_wind.differentiate('longitude')

    horizontal_shear = np.sqrt(u_lon_gradient**2 + v_lat_gradient**2)
    return horizontal_shear.isel(valid_time=0).squeeze()

def calculate_general_wind_shear(vertical_shear, horizontal_shear):
    """
    Calculate general wind shear from vertical and horizontal wind shear.

    Args:
        vertical_shear (xr.DataArray): The vertical wind shear data.
        horizontal_shear (xr.DataArray): The horizontal wind shear data.

    Returns:
        xr.DataArray: The calculated general wind shear.
    """
    return np.sqrt(horizontal_shear**2 + vertical_shear**2)

def classify_turbulence(shear_value):
    """
    Classify turbulence level based on wind shear value.

    Args:
        shear_value (float): The wind shear value.

    Returns:
        int: The turbulence level (0: Light, 1: Moderate, 2: Severe, 3: Extreme).
    """
    if shear_value < 5:
        return 0  # Light
    elif shear_value < 10:
        return 1  # Moderate
    elif shear_value < 15:
        return 2  # Severe
    else:
        return 3  # Extreme
    

def plot_turbulence_level(data, filename, continent = [71.0, -31.0, 36.0, 40.0]):
    """
    Plot turbulence level data on a map.

    Args:
        data (xr.DataArray): The turbulence level data to plot.
        filename (str): The name of the file to save the plot.
        continent (list, optional): The geographical area in plot format [West, East, South, North]. Defaults to Europe.
    """
    cmap = ListedColormap(['blue', 'green', 'orange', 'red'])
    norm = BoundaryNorm([0, 1, 2, 3, 4], cmap.N)

    fig, ax = plt.subplots(figsize=(10, 6), subplot_kw={'projection': ccrs.PlateCarree()})
    ax.set_extent(convert_api_to_plot_format(continent), crs=ccrs.PlateCarree())  # Europe

    c = ax.pcolormesh(data['longitude'], data['latitude'], data, cmap=cmap, norm=norm, shading='auto')

    ax.coastlines(resolution='10m')
    ax.gridlines(draw_labels=True)

    ax.set_title('Turbulence Level Based on General Wind Shear')
    cbar = plt.colorbar(c, ax=ax, orientation='vertical', ticks=[0.5, 1.5, 2.5, 3.5], label='Turbulence Level')
    cbar.ax.set_yticklabels(['Light', 'Moderate', 'Severe', 'Extreme'])

    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.show()

def main():
    """
    Main function to download data, calculate wind shear and turbulence, and plot the results.
    """
    date = datetime.datetime(2024, 11, 15)
    time = datetime.datetime.strptime('10:00', '%H:%M').time()
    area = [71.0, -31.0, 36.0, 40.0]  # Europe bounding box (North, West, South, East)

    data = download_era5_data(date, time, area)

    vertical_shear = calculate_wind_shear(data)
    plot_wind_shear(vertical_shear, 'Vertical Wind Shear', 'vertical_wind_shear.png')

    horizontal_shear = calculate_horizontal_shear(data)
    plot_wind_shear(horizontal_shear, 'Horizontal Wind Shear', 'horizontal_wind_shear.png')

    general_wind_shear = calculate_general_wind_shear(vertical_shear, horizontal_shear)
    plot_wind_shear(general_wind_shear, 'General Wind Shear (Vertical + Horizontal)', 'general_wind_shear.png')

    turbulence = np.vectorize(classify_turbulence)(general_wind_shear)
    turbulence_data = xr.DataArray(turbulence, coords=[general_wind_shear['latitude'], general_wind_shear['longitude']], dims=['latitude', 'longitude'])
    plot_turbulence_level(turbulence_data, 'turbulence_level.png')

if __name__ == '__main__':
    main()