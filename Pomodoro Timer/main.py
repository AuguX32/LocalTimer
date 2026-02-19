from flask import Flask, render_template, jsonify, request
import threading
import time 

app = Flask(__name__)

# Nos variables Python qui seront influencées par le HTML
seconds_remaining = 1500  # 25 minutes en secondes
work_value = 1500 # Durée par défaut du travail
pause_value = 300  # 5 minutes en secondes
current_total_time = 1500 # Total pour la barre de progression
is_running = False
mode = "work" # Peut être 'work' ou 'break'

def countdown():
    global seconds_remaining, is_running, mode, current_total_time
    while True:
        if is_running and seconds_remaining > 0:
            time.sleep(1)
            seconds_remaining -= 1
        elif is_running and seconds_remaining == 0:
            # Le minuteur est arrivé à 0
            time.sleep(1) # Petite pause pour laisser le frontend afficher 00:00 et sonner
            
            if mode == "work":
                # Fin du travail : on passe en mode Pause, on remet 5 min, et on arrête
                mode = "break"
                seconds_remaining = pause_value
                current_total_time = pause_value
                is_running = False
            elif mode == "break":
                # Fin de la pause : on passe en mode Travail, on remet 25 min, et on DÉMARRE
                mode = "work"
                seconds_remaining = work_value
                current_total_time = work_value
                is_running = True

        else:
            time.sleep(0.5) # Pause légère pour ne pas surcharger le processeur

@app.route('/')
def index():
    # On transforme les secondes en format texte "25:00" pour l'affichage
    timer_display = f"{seconds_remaining // 60:02d}:{seconds_remaining % 60:02d}"
    pause_display = f"{pause_value // 60:02d}:{pause_value % 60:02d}"
    
    return render_template('index.html', timer=timer_display, pause=pause_display)

@app.route('/start', methods=['POST'])
def start_timer():
    global is_running
    is_running = True
    return jsonify(status="started")

@app.route('/pause', methods=['POST'])
def pause_timer():
    global is_running
    is_running = False
    return jsonify(status="paused")

@app.route('/reset', methods=['POST'])
def reset_timer():
    global seconds_remaining, is_running, mode, current_total_time
    is_running = False
    mode = "work"
    seconds_remaining = work_value
    current_total_time = work_value
    return jsonify(status="reset", time=f"{work_value//60:02d}:{work_value%60:02d}")

@app.route('/adjust_time', methods=['POST'])
def adjust_time():
    global seconds_remaining, current_total_time
    data = request.get_json()
    seconds_remaining += data.get('delta', 0)
    if seconds_remaining < 0: seconds_remaining = 0
    # Si on dépasse le total actuel, on met à jour le total pour que la barre ne soit pas bloquée à 100%
    if seconds_remaining > current_total_time:
        current_total_time = seconds_remaining
    return jsonify(status="adjusted")

@app.route('/adjust_pause', methods=['POST'])
def adjust_pause():
    global pause_value
    data = request.get_json()
    pause_value += data.get('delta', 0)
    if pause_value < 60: pause_value = 60 # Minimum 1 minute
    m = pause_value // 60
    s = pause_value % 60
    return jsonify(status="adjusted", time=f"{m:02d}:{s:02d}")

@app.route('/get_time')
def get_time():
    # On transforme les secondes en format MM:SS
    minutes = seconds_remaining // 60
    secondes = seconds_remaining % 60
    
    return jsonify(time=f"{minutes:02d}:{secondes:02d}", seconds=seconds_remaining, total=current_total_time, mode=mode, is_running=is_running)



if __name__ == '__main__':
    # Lancer le compte à rebours ici pour éviter qu'il ne se lance deux fois avec le debug
    threading.Thread(target=countdown, daemon=True).start()
    app.run(port=5000, debug=True)