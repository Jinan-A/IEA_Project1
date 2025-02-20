import React, { useEffect, useState } from "react";
import io from "socket.io-client";
import "./Grid.css";

const socket = io("http://localhost:5000");

const Grid = ({ size = 10 }) => {
    const [agents, setAgents] = useState([]);

    useEffect(() => {
        socket.on("agents_update", (updatedAgents) => {
            setAgents(updatedAgents);
        });

        return () => socket.off("agents_update");
    }, []);

    const startFormation = () => {
        socket.emit("start_formation");  // Triggers heuristic movement
    };

    const resetFormation = () => {
        socket.emit("reset_formation");  // Resets agents to start positions
    };

    return (
        <div className="container">
            <div className="button-container">
                <button className="start-button" onClick={startFormation}>Start Formation</button>
                <button className="reset-button" onClick={resetFormation}>Reset</button>
            </div>
            <div className="grid">
                {Array.from({ length: size }, (_, y) =>
                    Array.from({ length: size }, (_, x) => {
                        const isAgent = agents.some(agent => agent.x === x && agent.y === y);
                        return (
                            <div key={`${x}-${y}`} className={`cell ${isAgent ? "agent" : ""}`} />
                        );
                    })
                )}
            </div>
        </div>
    );
};

export default Grid;
