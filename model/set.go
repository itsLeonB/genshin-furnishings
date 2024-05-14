package model

import "go.mongodb.org/mongo-driver/bson/primitive"

type Set struct {
	ID         primitive.ObjectID `json:"id"`
	Name       string             `json:"name"`
	Materials  []Furnishing       `json:"materials"`
	Type       string             `json:"type"`
	Characters []Character        `json:"characters"`
}
