# helpers/chart_utils.py
import matplotlib
matplotlib.use('Agg')  # for headless servers
import matplotlib.pyplot as plt
from io import BytesIO
import base64

def plot_to_img():
    buffer = BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    plt.close()
    return base64.b64encode(image_png).decode('utf-8')
