#!/usr/bin/env python3

from flask import Flask, request, jsonify

# Import the participant class
from participant.simple_participant import SQLiteParticipant

# Flask app for participant
app = Flask(__name__)

# Global participant instance
participant_instance = None

def set_participant(participant):
    """Set the participant instance for the Flask app"""
    global participant_instance
    participant_instance = participant

@app.route('/begin', methods=['POST'])
def begin():
    """Begin a new transaction"""
    data = request.json
    result = participant_instance.begin_transaction(data['transaction_id'])
    return jsonify(result)

@app.route('/prepare', methods=['POST'])
def prepare():
    """Prepare phase of 2PC"""
    data = request.json
    result = participant_instance.prepare(
        transaction_id=data['transaction_id'],
        operations=data['operations']
    )
    return jsonify(result)

@app.route('/commit', methods=['POST'])
def commit():
    """Commit phase of 2PC"""
    data = request.json
    result = participant_instance.commit(data['transaction_id'])
    return jsonify(result)

@app.route('/abort', methods=['POST'])
def abort():
    """Abort a transaction"""
    data = request.json
    result = participant_instance.abort(data['transaction_id'])
    return jsonify(result)

@app.route('/status/<transaction_id>', methods=['GET'])
def get_status(transaction_id):
    """Get transaction status"""
    result = participant_instance.get_status(transaction_id)
    return jsonify(result)

@app.route('/resource/<key>', methods=['GET'])
def get_resource(key):
    """Get resource value"""
    result = participant_instance.get_resource(key)
    return jsonify(result)
