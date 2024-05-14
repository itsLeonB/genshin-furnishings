package model

import "go.mongodb.org/mongo-driver/bson/primitive"

type Furnishing struct {
	ID     primitive.ObjectID `json:"id"`
	Name   string             `json:"name"`
	Recipe []Material         `json:"recipe"`
	Amount int                `json:"amount"`
}
