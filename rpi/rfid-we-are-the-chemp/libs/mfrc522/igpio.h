// Copyright (C) 2021 twyleg
#pragma once

#include <cstddef>

namespace mfrc522 {

struct IGpio {

	enum class Value {
		LOW = 0,
		HIGH = 1
	};

	virtual void setValue(Value) = 0;
	virtual Value getValue() = 0;
};

}
