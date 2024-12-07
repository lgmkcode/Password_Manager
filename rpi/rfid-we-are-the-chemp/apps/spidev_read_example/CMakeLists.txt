set(TARGET_NAME spidev_read_example)

#
# set cmake settings
#
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_INCLUDE_CURRENT_DIR ON)

#
# add source files to target
#
add_executable(${TARGET_NAME}
	main.cc
	spidev_impl.h
	sys_gpio_impl.h
)

#
# link against libs
#
target_link_libraries(${TARGET_NAME}
	spidevpp
	mfrc522
	mosquitto
)
